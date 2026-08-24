"""Unit coverage for Extractor evaluation scorer helpers."""

from __future__ import annotations

from uuid import uuid4

from nova.contracts.common import (
    Evidence,
    EvidenceSourceType,
    FieldPresence,
    UncertaintyFlag,
)
from nova.contracts.extraction import ExtractedField, ExtractionResult, ExtractionStatus
from nova.evaluation.extractor.dataset import ExtractorCase, GoldField
from nova.evaluation.extractor.scorer import score_case


def _field(
    name: str,
    *,
    presence: FieldPresence,
    value: str | None,
    confidence: float | None = 0.9,
) -> ExtractedField:
    evidence = []
    if presence == FieldPresence.KNOWN and value is not None:
        evidence = [
            Evidence(
                source_type=EvidenceSourceType.DOCUMENT_SPAN,
                snippet=value,
                page=1,
            )
        ]
    return ExtractedField(
        trace_id=uuid4(),
        field_name=name,
        value=value,
        presence=presence,
        confidence=confidence if presence == FieldPresence.KNOWN else None,
        uncertainty=(
            UncertaintyFlag.NONE
            if presence == FieldPresence.KNOWN
            else UncertaintyFlag.OTHER
        ),
        evidence=evidence,
    )


def test_score_case_detects_presence_mismatch() -> None:
    case = ExtractorCase(
        case_id="unit_presence",
        category="missing_fields",
        document_type="COMMERCIAL_INVOICE",
        required_fields=["invoice_number"],
        document_text="Invoice Number: INV-1",
        gold_fields={
            "invoice_number": GoldField(presence="MISSING", value=None),
        },
        expected_status=("PARTIAL",),
        llm_response=None,
    )
    result = ExtractionResult(
        trace_id=uuid4(),
        document_id=uuid4(),
        document_version_id=uuid4(),
        shipment_id=uuid4(),
        status=ExtractionStatus.PARTIAL,
        fields=[
            _field("invoice_number", presence=FieldPresence.KNOWN, value="INV-1"),
        ],
    )
    score = score_case(case, result)
    assert not score.passed
    assert any("presence" in f for f in score.failures)
