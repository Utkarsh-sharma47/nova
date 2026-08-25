"""Parse and sanitize LLM JSON into ExtractionResult field contracts."""

from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from nova.contracts.common import (
    ConfidenceBand,
    ConfidenceSource,
    DocumentContent,
    Evidence,
    EvidenceSourceType,
    FieldPresence,
    UncertaintyCode,
    UncertaintyFlag,
)
from nova.contracts.extraction import ExtractedField
from nova.extraction.fields import is_supported_field
from nova.llm.errors import LLMOutputError

_WHITESPACE = re.compile(r"\s+")


def parse_llm_fields_payload(raw: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMOutputError("LLM output is not valid JSON") from exc
    if not isinstance(data, dict):
        raise LLMOutputError("LLM output must be a JSON object")
    fields = data.get("fields")
    if not isinstance(fields, list):
        raise LLMOutputError("LLM output missing fields array")
    return fields


def normalize_field_dicts(
    raw_fields: list[dict[str, Any]],
    *,
    required_fields: list[str],
    trace_id: UUID,
    document_id: UUID,
    document_version_id: UUID,
    shipment_id: UUID,
    run_id: UUID | None,
    agent_execution_id: UUID | None,
    content: DocumentContent,
) -> tuple[list[ExtractedField], list[str]]:
    """Validate, anti-fabricate, and fill missing required fields."""
    warnings: list[str] = []
    by_name: dict[str, ExtractedField] = {}
    document_text = _combined_text(content)

    for index, raw in enumerate(raw_fields):
        if not isinstance(raw, dict):
            warnings.append(f"ignored_non_object_field:{index}")
            continue
        name = raw.get("field_name") or raw.get("name")
        if not isinstance(name, str) or not name.strip():
            warnings.append(f"ignored_unnamed_field:{index}")
            continue
        name = name.strip()
        if not is_supported_field(name):
            warnings.append(f"rejected_unsupported_field:{name}")
            continue
        if name not in required_fields:
            warnings.append(f"rejected_unrequested_field:{name}")
            continue
        try:
            field = _build_field(
                raw,
                field_name=name,
                trace_id=trace_id,
                document_id=document_id,
                document_version_id=document_version_id,
                shipment_id=shipment_id,
                run_id=run_id,
                agent_execution_id=agent_execution_id,
                document_text=document_text,
            )
        except (ValidationError, ValueError, TypeError) as exc:
            warnings.append(f"field_schema_rejected:{name}:{exc}")
            by_name[name] = _unknown_field(
                name,
                trace_id=trace_id,
                document_id=document_id,
                document_version_id=document_version_id,
                shipment_id=shipment_id,
                run_id=run_id,
                agent_execution_id=agent_execution_id,
                reason="schema_rejected",
            )
            continue
        by_name[name] = field

    ordered: list[ExtractedField] = []
    for name in required_fields:
        if name in by_name:
            ordered.append(by_name[name])
        else:
            warnings.append(f"missing_required_field_filled_unknown:{name}")
            ordered.append(
                _unknown_field(
                    name,
                    trace_id=trace_id,
                    document_id=document_id,
                    document_version_id=document_version_id,
                    shipment_id=shipment_id,
                    run_id=run_id,
                    agent_execution_id=agent_execution_id,
                    reason="not_returned_by_model",
                )
            )
    return ordered, warnings


def _build_field(
    raw: dict[str, Any],
    *,
    field_name: str,
    trace_id: UUID,
    document_id: UUID,
    document_version_id: UUID,
    shipment_id: UUID,
    run_id: UUID | None,
    agent_execution_id: UUID | None,
    document_text: str,
) -> ExtractedField:
    presence = _parse_presence(raw.get("presence"))
    value = raw.get("value")
    confidence = raw.get("confidence")
    uncertainty = _parse_uncertainty(raw.get("uncertainty"))
    evidence_raw = raw.get("evidence") or []
    if isinstance(evidence_raw, dict):
        evidence_raw = [evidence_raw]
    if not isinstance(evidence_raw, list):
        evidence_raw = []

    evidence: list[Evidence] = [
        item
        for item in (
            _parse_evidence(raw_item, document_id=document_id) for raw_item in evidence_raw
        )
        if item is not None
    ]

    # Anti-fabrication: KNOWN requires grounded evidence present in document text.
    if presence == FieldPresence.KNOWN:
        if value is None or (isinstance(value, str) and not value.strip()):
            presence = FieldPresence.UNKNOWN
            value = None
            evidence = []
            uncertainty = UncertaintyFlag.OTHER
        else:
            grounded = _grounded_evidence(evidence, document_text)
            if not grounded:
                # Downgrade rather than accept fabricated grounding.
                presence = FieldPresence.UNKNOWN
                value = None
                evidence = []
                uncertainty = UncertaintyFlag.PARTIAL_EVIDENCE
            else:
                evidence = grounded

    if presence != FieldPresence.KNOWN:
        value = None
        if presence == FieldPresence.MISSING:
            uncertainty = (
                UncertaintyFlag.NONE if uncertainty == UncertaintyFlag.NONE else uncertainty
            )
        evidence = [
            item
            for item in evidence
            if item.source_type == EvidenceSourceType.NONE
            or (item.snippet and _snippet_in_text(item.snippet, document_text))
        ]

    confidence_band = _band(confidence)
    codes = _codes_for(presence, uncertainty, confidence)

    return ExtractedField(
        trace_id=trace_id,
        run_id=run_id,
        agent_execution_id=agent_execution_id,
        document_id=document_id,
        document_version_id=document_version_id,
        shipment_id=shipment_id,
        field_name=field_name,
        value=value,
        value_type=str(raw.get("value_type") or "string"),
        presence=presence,
        confidence=float(confidence) if confidence is not None else None,
        confidence_band=confidence_band,
        confidence_source=ConfidenceSource.MODEL,
        uncertainty=uncertainty,
        uncertainty_codes=codes,
        evidence=evidence,
        source_location=raw.get("source_location")
        if isinstance(raw.get("source_location"), dict)
        else None,
        warnings=[str(w) for w in raw.get("warnings") or [] if w is not None],
        candidates=raw.get("candidates") if isinstance(raw.get("candidates"), list) else None,
    )


def _parse_evidence(item: Any, *, document_id: UUID) -> Evidence | None:
    if not isinstance(item, dict):
        return None
    try:
        source_type = EvidenceSourceType(
            str(item.get("source_type") or item.get("evidence_type") or "NONE")
        )
    except ValueError:
        source_type = EvidenceSourceType.NONE
    page = item.get("page") if item.get("page") is not None else item.get("page_number")
    return Evidence(
        evidence_id=str(item["evidence_id"]) if item.get("evidence_id") else None,
        document_id=document_id,
        source_type=source_type,
        snippet=str(item["snippet"]) if item.get("snippet") is not None else None,
        page=int(page) if page is not None else None,
        page_number=int(page) if page is not None else None,
        bbox=item.get("bbox") if isinstance(item.get("bbox"), list) else None,
        locator=str(item["locator"]) if item.get("locator") else None,
        notes=str(item["notes"]) if item.get("notes") else None,
    )


def _grounded_evidence(evidence: list[Evidence], document_text: str) -> list[Evidence]:
    grounded: list[Evidence] = []
    for item in evidence:
        if item.source_type == EvidenceSourceType.NONE:
            continue
        if not item.snippet:
            continue
        if not _snippet_in_text(item.snippet, document_text):
            continue
        grounded.append(item)
    return grounded


def _snippet_in_text(snippet: str, document_text: str) -> bool:
    needle = _WHITESPACE.sub(" ", snippet).strip().lower()
    haystack = _WHITESPACE.sub(" ", document_text).strip().lower()
    if not needle or not haystack:
        return False
    return needle in haystack


def _unknown_field(
    name: str,
    *,
    trace_id: UUID,
    document_id: UUID,
    document_version_id: UUID,
    shipment_id: UUID,
    run_id: UUID | None,
    agent_execution_id: UUID | None,
    reason: str,
) -> ExtractedField:
    return ExtractedField(
        trace_id=trace_id,
        run_id=run_id,
        agent_execution_id=agent_execution_id,
        document_id=document_id,
        document_version_id=document_version_id,
        shipment_id=shipment_id,
        field_name=name,
        value=None,
        presence=FieldPresence.UNKNOWN,
        confidence=None,
        confidence_band=ConfidenceBand.UNKNOWN,
        confidence_source=ConfidenceSource.UNKNOWN,
        uncertainty=UncertaintyFlag.OTHER,
        uncertainty_codes=[UncertaintyCode.UNKNOWN],
        evidence=[],
        warnings=[reason],
    )


def _parse_presence(value: Any) -> FieldPresence:
    if value is None:
        return FieldPresence.UNKNOWN
    try:
        return FieldPresence(str(value).upper())
    except ValueError:
        return FieldPresence.UNKNOWN


def _parse_uncertainty(value: Any) -> UncertaintyFlag:
    if value is None:
        return UncertaintyFlag.NONE
    try:
        return UncertaintyFlag(str(value).upper())
    except ValueError:
        return UncertaintyFlag.OTHER


def _band(confidence: Any) -> ConfidenceBand:
    if confidence is None:
        return ConfidenceBand.UNKNOWN
    try:
        score = float(confidence)
    except (TypeError, ValueError):
        return ConfidenceBand.UNKNOWN
    if score >= 0.85:
        return ConfidenceBand.HIGH
    if score >= 0.60:
        return ConfidenceBand.MEDIUM
    return ConfidenceBand.LOW


def _codes_for(
    presence: FieldPresence,
    uncertainty: UncertaintyFlag,
    confidence: Any,
) -> list[UncertaintyCode]:
    codes: list[UncertaintyCode] = []
    if presence == FieldPresence.MISSING:
        codes.append(UncertaintyCode.MISSING)
    elif presence == FieldPresence.AMBIGUOUS:
        codes.append(UncertaintyCode.AMBIGUOUS)
    elif presence == FieldPresence.UNKNOWN:
        codes.append(UncertaintyCode.UNKNOWN)
    if uncertainty == UncertaintyFlag.LOW_CONFIDENCE:
        codes.append(UncertaintyCode.LOW_CONFIDENCE)
    if uncertainty == UncertaintyFlag.CONFLICTING_EVIDENCE:
        codes.append(UncertaintyCode.CONTRADICTORY)
    if confidence is not None:
        try:
            if float(confidence) < 0.60:
                codes.append(UncertaintyCode.LOW_CONFIDENCE)
        except (TypeError, ValueError):
            pass
    if not codes:
        codes.append(UncertaintyCode.NONE)
    # dedupe
    seen: set[UncertaintyCode] = set()
    out: list[UncertaintyCode] = []
    for code in codes:
        if code not in seen:
            seen.add(code)
            out.append(code)
    return out


def _combined_text(content: DocumentContent) -> str:
    parts: list[str] = []
    if content.text:
        parts.append(content.text)
    if content.page_texts:
        parts.extend(content.page_texts)
    return "\n".join(parts)
