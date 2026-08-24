"""Deterministic validator unit coverage."""

from __future__ import annotations

from uuid import uuid4

from nova.agents.validator import ValidatorAgent
from nova.contracts.common import (
    ConfidenceBand,
    Evidence,
    EvidenceSourceType,
    FieldPresence,
    UncertaintyFlag,
)
from nova.contracts.extraction import ExtractedField
from nova.contracts.validation import (
    CustomerRuleSnapshot,
    ValidationOutcome,
    ValidationRequest,
)
from nova.validation_store import InMemoryValidationStore


def _known(name: str, value: object) -> ExtractedField:
    return ExtractedField(
        trace_id=uuid4(),
        field_name=name,
        value=value,
        presence=FieldPresence.KNOWN,
        confidence=0.95,
        confidence_band=ConfidenceBand.HIGH,
        uncertainty=UncertaintyFlag.NONE,
        evidence=[
            Evidence(source_type=EvidenceSourceType.DOCUMENT_SPAN, snippet=str(value), page=1)
        ],
    )


def test_numeric_and_date_and_format_paths() -> None:
    rules = [
        CustomerRuleSnapshot(
            trace_id=uuid4(),
            rule_id=uuid4(),
            rule_code="FMT",
            version="1",
            severity="HIGH",
            expression={"op": "format", "field": "bl_number", "pattern": r"^BL-[0-9]+$"},
        ),
        CustomerRuleSnapshot(
            trace_id=uuid4(),
            rule_id=uuid4(),
            rule_code="NUM",
            version="1",
            severity="HIGH",
            expression={"op": "numeric", "field": "weight_kg", "expected": 100, "tolerance_abs": 1},
        ),
        CustomerRuleSnapshot(
            trace_id=uuid4(),
            rule_id=uuid4(),
            rule_code="DATE",
            version="1",
            severity="HIGH",
            expression={"op": "date", "field": "ship_date", "expected": "2026-01-15"},
        ),
    ]
    result = ValidatorAgent(store=InMemoryValidationStore()).validate(
        ValidationRequest(
            trace_id=uuid4(),
            run_id=uuid4(),
            document_id=uuid4(),
            document_version_id=uuid4(),
            shipment_id=uuid4(),
            customer_id=uuid4(),
            extraction_result_id=uuid4(),
            rules=rules,
            extracted_fields=[
                _known("bl_number", "BL-9"),
                _known("weight_kg", 100.5),
                _known("ship_date", "2026-01-15"),
            ],
        )
    )
    assert [c.outcome for c in result.checks] == [
        ValidationOutcome.MATCH,
        ValidationOutcome.MATCH,
        ValidationOutcome.MATCH,
    ]
