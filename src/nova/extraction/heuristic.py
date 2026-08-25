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


def heuristic_extractor_response(request: LLMRequest) -> dict[str, Any]:
    user = next((msg.content for msg in request.messages if msg.role == "user"), "")
    required = _extract_required_fields(user)
    document_text = _extract_document_text(user)
    fields: list[dict[str, Any]] = []
    for name in required:
        if not is_supported_field(name):
            continue
        match = _find_value(name, document_text)
        if match is None:
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
        value, snippet, alias = match
        confidence = _confidence_from_evidence(field_name=name, alias=alias, value=value)
        fields.append(
            {
                "field_name": name,
                "value": value,
                "value_type": "string",
                "presence": "KNOWN",
                "confidence": confidence,
                "uncertainty": "NONE" if confidence >= 0.85 else "LOW_CONFIDENCE",
                "evidence": [
                    {
                        "evidence_id": f"h-{name}",
                        "source_type": "DOCUMENT_SPAN",
                        "snippet": snippet,
                        "page": 1,
                    }
                ],
                "warnings": [],
            }
        )
    return {"fields": fields}


def _confidence_from_evidence(*, field_name: str, alias: str, value: str) -> float:
    """Score extraction confidence from label specificity and value clarity."""
    aliases = _FIELD_ALIASES.get(field_name, (field_name.replace("_", " "),))
    alias_key = alias.strip().lower()
    try:
        rank = next(i for i, item in enumerate(aliases) if item.lower() == alias_key)
    except StopIteration:
        rank = len(aliases)

    # Preferred canonical labels score higher than trailing short aliases.
    span = max(len(aliases) - 1, 1)
    specificity = 1.0 - (rank / (span + 1.0))
    score = 0.82 + (0.16 * specificity)

    if alias_key in _WEAK_ALIASES or len(alias_key) <= 3:
        score -= 0.10

    value_text = value.strip()
    lower = value_text.lower()
    if any(marker in value_text for marker in ("?", "~", "???")):
        score -= 0.12
    if " or " in lower or ("/" in value_text and any(ch in value_text for ch in "?~")):
        score -= 0.08
    if "ignore" in lower or "#####" in value_text:
        score -= 0.15
    if len(value_text) < 2:
        score -= 0.05

    # Exact preferred label + clean value stays in the high band.
    if rank == 0 and alias_key not in _WEAK_ALIASES:
        score = max(score, 0.93)

    return round(min(0.99, max(0.55, score)), 4)


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


def _find_value(field_name: str, text: str) -> tuple[str, str, str] | None:
    aliases = _FIELD_ALIASES.get(field_name, (field_name.replace("_", " "),))
    for alias in aliases:
        pattern = re.compile(
            rf"(?im)^\s*{re.escape(alias)}\s*[:\-]\s*(.+?)\s*$",
        )
        found = pattern.search(text)
        if found:
            value = found.group(1).strip()
            if value:
                snippet = found.group(0).strip()
                return value, snippet, alias
    return None
