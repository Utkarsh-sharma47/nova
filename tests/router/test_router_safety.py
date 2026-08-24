"""Unit tests for Router safety and dispositions."""

from __future__ import annotations

from uuid import uuid4

from nova.contracts.common import (
    Evidence,
    EvidenceSourceType,
    FieldPresence,
    UncertaintyFlag,
)
from nova.contracts.extraction import ExtractedField, ExtractionResult, ExtractionStatus
from nova.contracts.routing import (
    DecisionKind,
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
from nova.router import RouterService


def _ids() -> dict[str, object]:
    return {
        "trace_id": uuid4(),
        "run_id": uuid4(),
        "document_id": uuid4(),
        "document_version_id": uuid4(),
        "shipment_id": uuid4(),
        "verification_run_id": uuid4(),
        "validation_result_id": uuid4(),
    }


def _known(trace_id, name: str, value: str, conf: float = 0.95) -> ExtractedField:
    return ExtractedField(
        trace_id=trace_id,
        field_name=name,
        value=value,
        presence=FieldPresence.KNOWN,
        confidence=conf,
        uncertainty=UncertaintyFlag.NONE,
        evidence=[
            Evidence(
                evidence_id=f"e-{name}",
                source_type=EvidenceSourceType.DOCUMENT_SPAN,
                snippet=value,
                page=1,
            )
        ],
    )


def _request(
    *,
    ids: dict[str, object] | None = None,
    fields: list[ExtractedField] | None = None,
    checks: list[ValidationCheck] | None = None,
    extraction_status: ExtractionStatus = ExtractionStatus.SUCCEEDED,
    validation_status: ValidationStatus = ValidationStatus.COMPLETED,
    llm: LlmRoutingSuggestion | None = None,
    error_code: str | None = None,
) -> RoutingRequest:
    ids = ids or _ids()
    trace_id = ids["trace_id"]
    assert isinstance(trace_id, object)
    if fields is None:
        fields = [
            _known(trace_id, "bl_number", "BL-1"),
            _known(trace_id, "vessel", "NEPTUNE"),
        ]
    if checks is None:
        checks = [
            ValidationCheck(
                trace_id=trace_id,  # type: ignore[arg-type]
                rule_id=uuid4(),
                rule_code="BL_REQUIRED",
                field_name="bl_number",
                outcome=ValidationOutcome.MATCH,
                reason="ok",
            ),
            ValidationCheck(
                trace_id=trace_id,  # type: ignore[arg-type]
                rule_id=uuid4(),
                rule_code="VESSEL_REQUIRED",
                field_name="vessel",
                outcome=ValidationOutcome.MATCH,
                reason="ok",
            ),
        ]
    extraction_kwargs: dict[str, object] = {}
    if extraction_status == ExtractionStatus.FAILED:
        extraction_kwargs["error_code"] = error_code or "E"
        extraction_kwargs["error_message"] = "failed"
    validation_kwargs: dict[str, object] = {
        "match_count": sum(1 for c in checks if c.outcome == ValidationOutcome.MATCH),
        "mismatch_count": sum(1 for c in checks if c.outcome == ValidationOutcome.MISMATCH),
        "uncertain_count": sum(1 for c in checks if c.outcome == ValidationOutcome.UNCERTAIN),
    }
    if validation_status == ValidationStatus.FAILED:
        validation_kwargs["error_code"] = error_code or "V"
        validation_kwargs["error_message"] = "failed"

    return RoutingRequest(
        trace_id=trace_id,  # type: ignore[arg-type]
        run_id=ids["run_id"],  # type: ignore[arg-type]
        document_id=ids["document_id"],  # type: ignore[arg-type]
        document_version_id=ids["document_version_id"],  # type: ignore[arg-type]
        shipment_id=ids["shipment_id"],  # type: ignore[arg-type]
        verification_run_id=ids["verification_run_id"],  # type: ignore[arg-type]
        validation_result_id=ids["validation_result_id"],  # type: ignore[arg-type]
        extraction=ExtractionResult(
            trace_id=trace_id,  # type: ignore[arg-type]
            document_id=ids["document_id"],  # type: ignore[arg-type]
            document_version_id=ids["document_version_id"],  # type: ignore[arg-type]
            shipment_id=ids["shipment_id"],  # type: ignore[arg-type]
            status=extraction_status,
            fields=fields,
            **extraction_kwargs,  # type: ignore[arg-type]
        ),
        validation=ValidationResult(
            trace_id=trace_id,  # type: ignore[arg-type]
            document_id=ids["document_id"],  # type: ignore[arg-type]
            document_version_id=ids["document_version_id"],  # type: ignore[arg-type]
            shipment_id=ids["shipment_id"],  # type: ignore[arg-type]
            status=validation_status,
            checks=checks,
            engine_version="t",
            **validation_kwargs,  # type: ignore[arg-type]
        ),
        policy=RoutingPolicySnapshot(
            trace_id=trace_id,  # type: ignore[arg-type]
            policy_id="default",
            policy_version="1.0.0",
            critical_fields=["bl_number", "vessel"],
        ),
        llm_suggestion=llm,
    )


def test_auto_approve_happy_path() -> None:
    result = RouterService().decide(_request())
    assert result.decision is DecisionKind.AUTO_APPROVE
    assert result.safety_constraints_applied == []
    assert result.requires_human_attention is False


def test_mismatch_is_amendment() -> None:
    req = _request()
    req.validation.checks[0].outcome = ValidationOutcome.MISMATCH
    req.validation.mismatch_count = 1
    req.validation.match_count = 1
    result = RouterService().decide(req)
    assert result.decision is DecisionKind.AMENDMENT_REQUEST
    assert "SC_BLOCKING_MISMATCH" in result.safety_constraints_applied


def test_llm_cannot_auto_approve_on_mismatch() -> None:
    req = _request(
        llm=LlmRoutingSuggestion(
            trace_id=uuid4(),
            decision=DecisionKind.AUTO_APPROVE,
            rationale="looks fine",
            triggering_check_ids=["x"],
        )
    )
    req.validation.checks[0].outcome = ValidationOutcome.MISMATCH
    req.validation.mismatch_count = 1
    req.validation.match_count = 1
    result = RouterService().decide(req)
    assert result.decision is not DecisionKind.AUTO_APPROVE
    assert result.unsafe_llm_attempt is True
    assert result.llm_overridden is True


def test_failsafe_never_auto_approves() -> None:
    result = RouterService().decide(_request(), force_failsafe=True)
    assert result.decision is DecisionKind.HUMAN_REVIEW
    assert result.actor_type.value == "system_failsafe"


def test_idempotent_fingerprint() -> None:
    service = RouterService()
    req = _request()
    a = service.decide(req)
    b = service.decide(req)
    assert a.decision == b.decision
    assert a.input_fingerprint == b.input_fingerprint
