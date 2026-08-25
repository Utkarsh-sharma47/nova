"""Shared fixtures for Validator Agent tests."""

from __future__ import annotations

from uuid import UUID, uuid4

from nova.contracts.common import (
    ConfidenceBand,
    Evidence,
    EvidenceSourceType,
    FieldPresence,
    UncertaintyFlag,
)
from nova.contracts.extraction import ExtractedField
from nova.contracts.validation import CustomerRuleSnapshot, ValidationRequest


def ids() -> dict[str, UUID]:
    return {
        "trace_id": uuid4(),
        "run_id": uuid4(),
        "document_id": uuid4(),
        "document_version_id": uuid4(),
        "shipment_id": uuid4(),
        "customer_id": uuid4(),
    }


def known_field(
    trace_id: UUID,
    name: str = "bl_number",
    value: object = "BL-100",
    *,
    confidence: float = 0.95,
    evidence_id: str = "ev-1",
    uncertainty: UncertaintyFlag = UncertaintyFlag.NONE,
) -> ExtractedField:
    return ExtractedField(
        trace_id=trace_id,
        field_name=name,
        value=value,
        value_type="string",
        presence=FieldPresence.KNOWN,
        confidence=confidence,
        confidence_band=ConfidenceBand.HIGH,
        uncertainty=uncertainty,
        evidence=[
            Evidence(
                evidence_id=evidence_id,
                source_type=EvidenceSourceType.DOCUMENT_SPAN,
                snippet=str(value)[:80],
                page=1,
            )
        ],
    )


def missing_field(trace_id: UUID, name: str = "bl_number") -> ExtractedField:
    return ExtractedField(
        trace_id=trace_id,
        field_name=name,
        value=None,
        presence=FieldPresence.MISSING,
        confidence=None,
        uncertainty=UncertaintyFlag.NONE,
        evidence=[],
    )


def rule(
    *,
    trace_id: UUID,
    rule_code: str,
    expression: dict,
    requires_judgment: bool = False,
    severity: str = "BLOCKING",
    version: str = "1",
) -> CustomerRuleSnapshot:
    return CustomerRuleSnapshot(
        trace_id=trace_id,
        rule_id=uuid4(),
        rule_code=rule_code,
        version=version,
        severity=severity,
        blocking=True,
        requires_judgment=requires_judgment,
        expression=expression,
    )


def make_request(
    *,
    ctx: dict[str, UUID],
    rules: list[CustomerRuleSnapshot],
    fields: list[ExtractedField],
    timeout_ms: int = 30_000,
    extraction_status: str | None = None,
) -> ValidationRequest:
    return ValidationRequest(
        **ctx,
        extraction_result_id=uuid4(),
        ruleset_id="rules-demo",
        ruleset_version="1.0.0",
        rules=rules,
        extracted_fields=fields,
        timeout_ms=timeout_ms,
        extraction_status=extraction_status,
    )
