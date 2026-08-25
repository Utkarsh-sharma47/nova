"""Contract/schema tests for Nova domain models (no LLM, no DB)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from nova.contracts import (
    AuditEvent,
    DecisionKind,
    DecisionResult,
    DocumentContent,
    ErrorResponse,
    ErrorType,
    Evidence,
    ExtractedField,
    ExtractionRequest,
    ExtractionResult,
    ExtractionStatus,
    RoutingPolicySnapshot,
    RoutingRequest,
    UncertaintyCode,
    ValidationCheck,
    ValidationOutcome,
    ValidationRequest,
    ValidationResult,
)
from nova.contracts.audit import ActorType
from nova.contracts.common import (
    ConfidenceBand,
    EvidenceSourceType,
    FieldPresence,
    UncertaintyFlag,
)
from nova.contracts.routing import DecisionActorType
from nova.contracts.validation import CustomerRuleSnapshot


def _ids() -> dict[str, object]:
    return {
        "trace_id": uuid4(),
        "run_id": uuid4(),
        "document_id": uuid4(),
        "document_version_id": uuid4(),
        "shipment_id": uuid4(),
        "customer_id": uuid4(),
    }


def _content() -> DocumentContent:
    return DocumentContent(
        media_type="application/pdf",
        text="Bill of Lading sample",
        processor_name="passthrough",
        processor_version="1.0.0",
    )


def _known_field(trace_id, name: str = "bl_number", value: str = "BL-1") -> ExtractedField:
    return ExtractedField(
        trace_id=trace_id,
        field_name=name,
        value=value,
        presence=FieldPresence.KNOWN,
        confidence=0.92,
        confidence_band=ConfidenceBand.HIGH,
        uncertainty=UncertaintyFlag.NONE,
        evidence=[
            Evidence(
                source_type=EvidenceSourceType.DOCUMENT_SPAN,
                snippet=value,
                page=1,
            )
        ],
        uncertainty_codes=[UncertaintyCode.NONE],
    )


def test_extraction_round_trip() -> None:
    ids = _ids()
    req = ExtractionRequest(
        **ids,
        document_type="BILL_OF_LADING",
        content=_content(),
        required_fields=["bl_number", "vessel"],
    )
    ctx = {
        k: ids[k]
        for k in (
            "trace_id",
            "run_id",
            "document_id",
            "document_version_id",
            "shipment_id",
        )
    }
    result = ExtractionResult(
        **ctx,
        status=ExtractionStatus.COMPLETED,
        fields=[_known_field(ids["trace_id"])],
    )
    assert req.contract_version == "1.0.0"
    assert result.status is ExtractionStatus.SUCCEEDED
    assert result.fields[0].confidence == 0.92
    assert result.fields[0].presence is FieldPresence.KNOWN


def test_extraction_rejects_fabricated_known_null() -> None:
    with pytest.raises(ValidationError):
        ExtractedField(
            trace_id=uuid4(),
            field_name="x",
            value=None,
            presence=FieldPresence.KNOWN,
            confidence=0.9,
            evidence=[Evidence(source_type=EvidenceSourceType.DOCUMENT_SPAN, snippet="x")],
        )


def test_extraction_rejects_non_null_when_missing() -> None:
    with pytest.raises(ValidationError):
        ExtractedField(
            trace_id=uuid4(),
            field_name="x",
            value="invented",
            presence=FieldPresence.MISSING,
            confidence=None,
            uncertainty=UncertaintyFlag.NONE,
        )


def test_extraction_rejects_confidence_out_of_range() -> None:
    with pytest.raises(ValidationError):
        ExtractedField(
            trace_id=uuid4(),
            field_name="x",
            value="y",
            presence=FieldPresence.KNOWN,
            confidence=1.5,
            evidence=[Evidence(source_type=EvidenceSourceType.DOCUMENT_SPAN, snippet="y")],
        )


def test_validation_outcomes_and_part2_related_extractions() -> None:
    ids = _ids()
    rule_id = uuid4()
    field = _known_field(ids["trace_id"])
    req = ValidationRequest(
        **ids,
        extraction_result_id=uuid4(),
        rules=[
            CustomerRuleSnapshot(
                trace_id=ids["trace_id"],  # type: ignore[arg-type]
                rule_id=rule_id,
                rule_code="BL_REQUIRED",
                version="1",
                severity="HIGH",
                expression={"op": "required", "field": "bl_number"},
            )
        ],
        extracted_fields=[field],
        related_extractions=[],
    )
    result = ValidationResult(
        **{k: ids[k] for k in ("trace_id", "document_id", "document_version_id", "shipment_id")},
        extraction_result_id=req.extraction_result_id,
        checks=[
            ValidationCheck(
                trace_id=ids["trace_id"],  # type: ignore[arg-type]
                rule_id=rule_id,
                rule_code="BL_REQUIRED",
                field_name="bl_number",
                outcome=ValidationOutcome.MATCH,
                reason="present",
                deterministic=True,
            )
        ],
        match_count=1,
        engine_version="det-1",
    )
    assert req.related_extractions == []
    assert result.checks[0].outcome is ValidationOutcome.MATCH


def test_routing_policy_rejects_unknown_auto_approve_default_false() -> None:
    policy = RoutingPolicySnapshot(
        trace_id=uuid4(),
        policy_id="default",
        policy_version="1.0.0",
    )
    assert policy.allow_auto_approve_on_unknown is False


def test_routing_policy_threshold_order() -> None:
    with pytest.raises(ValidationError):
        RoutingPolicySnapshot(
            trace_id=uuid4(),
            policy_id="bad",
            policy_version="1",
            high_confidence_threshold=0.5,
            low_confidence_threshold=0.9,
        )


def test_decision_result_enums() -> None:
    ids = _ids()
    validation = ValidationResult(
        **{k: ids[k] for k in ("trace_id", "document_id", "document_version_id", "shipment_id")},
        extraction_result_id=uuid4(),
        engine_version="det-1",
    )
    extraction = ExtractionResult(
        **{k: ids[k] for k in ("trace_id", "document_id", "document_version_id", "shipment_id")},
        status=ExtractionStatus.SUCCEEDED,
        fields=[_known_field(ids["trace_id"])],  # type: ignore[arg-type]
    )
    decision = DecisionResult(
        **{k: ids[k] for k in ("trace_id", "document_id", "document_version_id", "shipment_id")},
        verification_run_id=ids["run_id"],  # type: ignore[arg-type]
        validation_result_id=uuid4(),
        decision=DecisionKind.HUMAN_REVIEW,
        reasons=["uncertain_field"],
        reason_codes=["UNCERTAIN_BLOCKING"],
        policy_id="default",
        policy_version="1.0.0",
        routing_rule_version="router-policy-1.0.0",
        agent_version="router-1.0.0",
        requires_human_attention=True,
        actor_type=DecisionActorType.ROUTER,
        input_fingerprint="abc",
        completed_at=datetime.now(UTC),
    )
    assert decision.requires_human_attention is True
    RoutingRequest(
        **{k: ids[k] for k in ("trace_id", "document_id", "document_version_id", "shipment_id")},
        verification_run_id=ids["run_id"],  # type: ignore[arg-type]
        validation_result_id=decision.validation_result_id,
        extraction=extraction,
        validation=validation,
        policy=RoutingPolicySnapshot(
            trace_id=ids["trace_id"],  # type: ignore[arg-type]
            policy_id="default",
            policy_version="1.0.0",
        ),
        blocking_uncertainty_present=True,
    )


def test_error_response_requires_retryable() -> None:
    err = ErrorResponse(
        error_type=ErrorType.AI_PROVIDER,
        error_code="AI_PROVIDER_TIMEOUT",
        message="Language model call timed out",
        trace_id=uuid4(),
        retryable=True,
    )
    assert err.retryable is True
    with pytest.raises(ValidationError):
        ErrorResponse(
            error_type=ErrorType.NOT_FOUND,
            error_code="NOT_FOUND_DOCUMENT",
            message="missing",
        )


def test_audit_event() -> None:
    event = AuditEvent(
        event_type="DECISION_RECORDED",
        actor_type=ActorType.AGENT,
        actor_id="router",
        entity_type="decision",
        entity_id=uuid4(),
        payload={"decision": "HUMAN_REVIEW"},
        trace_id=uuid4(),
        created_at=datetime.now(UTC),
    )
    assert event.contract_version == "1.0.0"


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        DocumentContent(
            media_type="text/plain",
            text="x",
            processor_name="p",
            processor_version="1",
            unexpected=True,  # type: ignore[call-arg]
        )
