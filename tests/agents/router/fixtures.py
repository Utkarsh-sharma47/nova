"""Shared fixtures for Router / Decision Agent tests."""

from __future__ import annotations

from uuid import uuid4

from nova.contracts.common import (
    ConfidenceBand,
    Evidence,
    EvidenceSourceType,
    FieldPresence,
    StageError,
    UncertaintyFlag,
)
from nova.contracts.extraction import ExtractedField, ExtractionResult, ExtractionStatus
from nova.contracts.routing import (
    LlmRoutingSuggestion,
    RoutingPolicySnapshot,
    RoutingRequest,
)
from nova.contracts.validation import (
    ValidationCheck,
    ValidationOutcome,
    ValidationResult,
    ValidationStatus,
)


def _ctx() -> dict[str, object]:
    return {
        "trace_id": uuid4(),
        "run_id": uuid4(),
        "document_id": uuid4(),
        "document_version_id": uuid4(),
        "shipment_id": uuid4(),
        "customer_id": uuid4(),
    }


def known_field(
    trace_id: object,
    name: str = "bl_number",
    value: str = "BL-1",
    *,
    confidence: float = 0.95,
    evidence: bool = True,
) -> ExtractedField:
    ev = []
    if evidence:
        ev = [
            Evidence(
                evidence_id=f"ev-{name}",
                source_type=EvidenceSourceType.DOCUMENT_SPAN,
                snippet=value,
                page=1,
            )
        ]
    return ExtractedField(
        trace_id=trace_id,  # type: ignore[arg-type]
        field_name=name,
        value=value,
        presence=FieldPresence.KNOWN,
        confidence=confidence,
        confidence_band=ConfidenceBand.HIGH,
        uncertainty=UncertaintyFlag.NONE,
        evidence=ev,
    )


def missing_field(trace_id: object, name: str = "bl_number") -> ExtractedField:
    return ExtractedField(
        trace_id=trace_id,  # type: ignore[arg-type]
        field_name=name,
        value=None,
        presence=FieldPresence.MISSING,
        confidence=None,
        uncertainty=UncertaintyFlag.NONE,
    )


def make_extraction(
    ctx: dict[str, object],
    *,
    status: ExtractionStatus = ExtractionStatus.SUCCEEDED,
    fields: list[ExtractedField] | None = None,
    error_code: str | None = None,
) -> ExtractionResult:
    errors: list[StageError] = []
    if status == ExtractionStatus.FAILED:
        errors = [
            StageError(
                code=error_code or "EXTRACTION_FAILED",
                message="extraction failed",
                retryable=False,
            )
        ]
    return ExtractionResult(
        trace_id=ctx["trace_id"],  # type: ignore[arg-type]
        run_id=ctx["run_id"],  # type: ignore[arg-type]
        document_id=ctx["document_id"],  # type: ignore[arg-type]
        document_version_id=ctx["document_version_id"],  # type: ignore[arg-type]
        shipment_id=ctx["shipment_id"],  # type: ignore[arg-type]
        status=status,
        fields=fields
        if fields is not None
        else [
            known_field(ctx["trace_id"]),
            known_field(ctx["trace_id"], "vessel", "OCEAN"),
        ],
        error_code=error_code,
        errors=errors,
    )


def make_validation(
    ctx: dict[str, object],
    *,
    status: ValidationStatus = ValidationStatus.COMPLETED,
    checks: list[ValidationCheck] | None = None,
    error_code: str | None = None,
) -> ValidationResult:
    default_checks = [
        ValidationCheck(
            trace_id=ctx["trace_id"],  # type: ignore[arg-type]
            rule_id=uuid4(),
            rule_code="BL_REQUIRED",
            field_name="bl_number",
            outcome=ValidationOutcome.MATCH,
            reason="present",
            blocking=True,
            confidence=0.99,
        ),
        ValidationCheck(
            trace_id=ctx["trace_id"],  # type: ignore[arg-type]
            rule_id=uuid4(),
            rule_code="VESSEL_REQUIRED",
            field_name="vessel",
            outcome=ValidationOutcome.MATCH,
            reason="present",
            blocking=True,
            confidence=0.99,
        ),
    ]
    final_checks = checks if checks is not None else default_checks
    match_count = sum(1 for c in final_checks if c.outcome == ValidationOutcome.MATCH)
    mismatch_count = sum(1 for c in final_checks if c.outcome == ValidationOutcome.MISMATCH)
    uncertain_count = sum(1 for c in final_checks if c.outcome == ValidationOutcome.UNCERTAIN)
    errors: list[StageError] = []
    if status == ValidationStatus.FAILED:
        errors = [
            StageError(
                code=error_code or "VALIDATION_FAILED",
                message="validation failed",
                retryable=False,
            )
        ]
    return ValidationResult(
        trace_id=ctx["trace_id"],  # type: ignore[arg-type]
        run_id=ctx["run_id"],  # type: ignore[arg-type]
        document_id=ctx["document_id"],  # type: ignore[arg-type]
        document_version_id=ctx["document_version_id"],  # type: ignore[arg-type]
        shipment_id=ctx["shipment_id"],  # type: ignore[arg-type]
        extraction_result_id=uuid4(),
        status=status,
        checks=final_checks,
        match_count=match_count,
        mismatch_count=mismatch_count,
        uncertain_count=uncertain_count,
        engine_version="det-1",
        error_code=error_code,
        errors=errors,
    )


def make_policy(ctx: dict[str, object], **overrides: object) -> RoutingPolicySnapshot:
    data: dict[str, object] = {
        "trace_id": ctx["trace_id"],
        "policy_id": "default",
        "policy_version": "1.0.0",
        "critical_fields": ["bl_number", "vessel"],
    }
    data.update(overrides)
    return RoutingPolicySnapshot(**data)  # type: ignore[arg-type]


def make_request(
    *,
    extraction: ExtractionResult | None = None,
    validation: ValidationResult | None = None,
    policy: RoutingPolicySnapshot | None = None,
    llm_suggestion: LlmRoutingSuggestion | None = None,
    blocking_uncertainty_present: bool = False,
    ctx: dict[str, object] | None = None,
) -> RoutingRequest:
    c = ctx or _ctx()
    extraction = extraction or make_extraction(c)
    validation = validation or make_validation(c)
    policy = policy or make_policy(c)
    return RoutingRequest(
        trace_id=c["trace_id"],  # type: ignore[arg-type]
        run_id=c["run_id"],  # type: ignore[arg-type]
        document_id=c["document_id"],  # type: ignore[arg-type]
        document_version_id=c["document_version_id"],  # type: ignore[arg-type]
        shipment_id=c["shipment_id"],  # type: ignore[arg-type]
        customer_id=c["customer_id"],  # type: ignore[arg-type]
        verification_run_id=c["run_id"],  # type: ignore[arg-type]
        validation_result_id=uuid4(),
        extraction=extraction,
        validation=validation,
        policy=policy,
        blocking_uncertainty_present=blocking_uncertainty_present,
        llm_suggestion=llm_suggestion,
    )
