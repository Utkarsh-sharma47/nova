"""Heuristic MockLLM factory for local/CI without API keys.

Parses simple ``Field: value`` lines from the document text embedded in the
prompt user message. Never invents values absent from the text.

Confidence is derived from match evidence (label specificity + value clarity),
not a constant.
"""

from __future__ import annotations

import json
import re
from typing import Any

from nova.extraction.fields import is_supported_field
from nova.llm.port import LLMRequest

_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "invoice_number": ("invoice number", "invoice #", "invoice no", "inv no", "inv#"),
    "invoice_date": ("invoice date", "date"),
    "seller_name": ("seller", "seller name", "from"),
    "buyer_name": ("buyer", "buyer name", "bill to"),
    "currency": ("currency", "ccy"),
    "total_amount": ("total amount", "amount due", "total", "amt"),
    "bl_number": ("bl number", "b/l number", "bill of lading", "bol"),
    "vessel_name": ("vessel", "vessel name", "ship"),
    "shipper_name": ("shipper", "shipper name"),
    "consignee_name": ("consignee", "consignee name"),
    "port_of_loading": ("port of loading", "load port", "pol"),
    "port_of_discharge": ("port of discharge", "discharge port", "pod"),
    "container_number": ("container number", "container no", "container"),
    "hs_code": ("hs code", "hs-code", "harmonized code", "hscode", "tariff code"),
    "incoterms": ("incoterms", "incoterm", "terms of delivery", "delivery terms"),
    "description_of_goods": (
        "description of goods",
        "goods description",
        "commodity",
        "description",
        "goods",
    ),
    "gross_weight": ("gross weight", "gross wt", "g.w.", "weight", "gw"),
}

# Short / ambiguous labels that are weak evidence even when they match.
_WEAK_ALIASES = frozenset(
    {
        "date",
        "from",
        "total",
        "amt",
        "ship",
        "pol",
        "pod",
        "gw",
        "ccy",
        "goods",
        "description",
        "weight",
        "container",
        "inv#",
        "inv no",
    }
)

# Expected value shape per field. A value that parses as its declared type is
# stronger evidence than free text; a value that fails its own type is weaker.
_FIELD_PATTERNS: dict[str, re.Pattern[str]] = {
    "invoice_number": re.compile(r"(?i)^[a-z0-9][a-z0-9\-_]{2,}$"),
    "invoice_date": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    "currency": re.compile(r"(?i)^[a-z]{3}$"),
    "total_amount": re.compile(r"^\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?$|^\d+(?:\.\d{1,2})?$"),
    "hs_code": re.compile(r"^\d{4}(?:\.\d{2}){1,2}$"),
    "incoterms": re.compile(r"(?i)^(?:fob|cif|cfr|exw|dap|ddp|fca|cpt|cip|fas)$"),
    "container_number": re.compile(r"(?i)^[a-z]{4}\d{7}$"),
    "gross_weight": re.compile(r"(?i)^\d+(?:\.\d+)?\s*(?:kg|kgs|t|mt|lb|lbs)$"),
    "bl_number": re.compile(r"(?i)^[a-z0-9][a-z0-9\-/]{3,}$"),
}

# Alternation between candidate values, e.g. "USD 15,200.00 OR 15200".
# Requires surrounding whitespace so that "18/08/2026" is not split.
_ALTERNATION = re.compile(r"(?i)\s+(?:or|/|\|)\s+")

_AMBIGUITY_MARKERS = ("?", "~", "maybe", "approx", "illegible", "unclear")
_NOISE_MARKERS = ("#####", "!!", "###")
_INJECTION_MARKERS = ("ignore previous", "ignore all", "auto approve", "ignore")

_BASE_EXACT_LABEL = 0.90
_CONFLICT_CEILING = 0.35
_HIGH_BAND = 0.85


def heuristic_extractor_response(request: LLMRequest) -> dict[str, Any]:
    user = next((msg.content for msg in request.messages if msg.role == "user"), "")
    required = _extract_required_fields(user)
    document_text = _extract_document_text(user)
    fields: list[dict[str, Any]] = []
    for name in required:
        if not is_supported_field(name):
            continue
        matches = _find_values(name, document_text)
        if not matches:
            fields.append(
                {
                    "field_name": name,
                    "value": None,
                    "value_type": "string",
                    "presence": "MISSING",
                    "confidence": None,
                    "uncertainty": "NONE",
                    "evidence": [],
                    "warnings": [],
                }
            )
            continue

        value, _snippet, alias = matches[0]
        evidence = [
            {
                "evidence_id": f"h-{name}-{index}",
                "source_type": "DOCUMENT_SPAN",
                "snippet": item[1],
                "page": 1,
            }
            for index, item in enumerate(matches)
        ]
        candidates = _candidate_values(matches)
        confidence = _confidence_from_evidence(field_name=name, alias=alias, value=value)

        if len(candidates) > 1:
            # Conflicting candidates are ambiguous evidence, never a confident value.
            fields.append(
                {
                    "field_name": name,
                    "value": None,
                    "value_type": "string",
                    "presence": "AMBIGUOUS",
                    "confidence": round(min(confidence, _CONFLICT_CEILING), 4),
                    "uncertainty": "CONFLICTING_EVIDENCE",
                    "evidence": evidence,
                    "warnings": [f"conflicting_candidates:{len(candidates)}"],
                    "candidates": [{"value": candidate} for candidate in candidates],
                }
            )
            continue

        fields.append(
            {
                "field_name": name,
                "value": value,
                "value_type": "string",
                "presence": "KNOWN",
                "confidence": confidence,
                "uncertainty": "NONE" if confidence >= _HIGH_BAND else "LOW_CONFIDENCE",
                "evidence": evidence,
                "warnings": [],
            }
        )
    return {"fields": fields}


def _candidate_values(matches: list[tuple[str, str, str]]) -> list[str]:
    """Distinct candidate values from repeated labels and inline alternations."""
    candidates: list[str] = []
    for value, _snippet, _alias in matches:
        for part in _ALTERNATION.split(value):
            cleaned = part.strip().strip('"').strip()
            if not cleaned:
                continue
            key = re.sub(r"[^a-z0-9]", "", cleaned.lower())
            if not key:
                continue
            if all(key != re.sub(r"[^a-z0-9]", "", c.lower()) for c in candidates):
                candidates.append(cleaned)
    return candidates


def _confidence_from_evidence(*, field_name: str, alias: str, value: str) -> float:
    """Score extraction confidence from the quality of the matched evidence.

    Signals, all read from the document itself: how specific the matched label
    was, whether the value parses as the field's declared type, and whether the
    value carries ambiguity/OCR-noise/instruction text. There is no floor that
    forces a canonical label into the high band.
    """
    aliases = _FIELD_ALIASES.get(field_name, (field_name.replace("_", " "),))
    alias_key = alias.strip().lower()
    try:
        rank = next(i for i, item in enumerate(aliases) if item.lower() == alias_key)
    except StopIteration:
        rank = len(aliases)

    score = _BASE_EXACT_LABEL
    # A trailing abbreviation is weaker evidence than the canonical label.
    score -= 0.04 * min(rank, 3)
    if alias_key in _WEAK_ALIASES or len(alias_key) <= 3:
        score -= 0.06

    value_text = value.strip()
    lower = value_text.lower()

    pattern = _FIELD_PATTERNS.get(field_name)
    if pattern is not None:
        score += 0.06 if pattern.match(value_text) else -0.12

    if any(marker in lower for marker in _AMBIGUITY_MARKERS):
        score -= 0.22
    if any(marker in value_text for marker in _NOISE_MARKERS):
        score -= 0.18
    if any(marker in lower for marker in _INJECTION_MARKERS):
        score -= 0.15
    if len(value_text) < 2:
        score -= 0.05
    if len(value_text) > 140:
        score -= 0.03

    return round(min(0.99, max(0.05, score)), 4)


def _extract_required_fields(user: str) -> list[str]:
    payload = _extract_user_payload(user)
    if payload is None:
        return []
    fields = payload.get("required_fields")
    if not isinstance(fields, list):
        return []
    return [str(item) for item in fields]


def _extract_document_text(user: str) -> str:
    payload = _extract_user_payload(user)
    if payload is None:
        return ""
    document = payload.get("document") or {}
    text = document.get("text")
    return text if isinstance(text, str) else ""


def _extract_user_payload(user: str) -> dict[str, Any] | None:
    """Locate the document JSON object (not the inline schema example braces)."""
    marker = user.find('"document_type_hint"')
    if marker < 0:
        marker = user.find('"required_fields"')
    if marker < 0:
        return None
    start = user.rfind("{", 0, marker)
    if start < 0:
        return None
    try:
        payload = json.loads(user[start:])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _find_values(field_name: str, text: str) -> list[tuple[str, str, str]]:
    """All ``label: value`` occurrences for a field, most specific label first.

    Returns every occurrence so that repeated labels carrying different values
    can be reported as conflicting evidence instead of silently taking the first.
    """
    aliases = _FIELD_ALIASES.get(field_name, (field_name.replace("_", " "),))
    matches: list[tuple[str, str, str]] = []
    for alias in aliases:
        pattern = re.compile(
            rf"(?im)^\s*{re.escape(alias)}\s*[:\-]\s*(.+?)\s*$",
        )
        for found in pattern.finditer(text):
            value = found.group(1).strip()
            if value:
                matches.append((value, found.group(0).strip(), alias))
        if matches:
            # Do not mix a specific label with looser aliases that may re-match
            # the same line under a different name.
            break
    return matches
