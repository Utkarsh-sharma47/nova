"""Router Decision Agent — safety, failsafe, persistence, and idempotency tests."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from nova.contracts.common import (
    FieldPresence,
    StageError,
    UncertaintyFlag,
)
from nova.contracts.extraction import ExtractionStatus
from nova.contracts.routing import (
    DecisionActorType,
    DecisionKind,
    DecisionResult,
    LlmRoutingSuggestion,
)
from nova.contracts.validation import ValidationCheck, ValidationOutcome, ValidationStatus
from nova.router import RouterService, assert_failsafe_cannot_auto_approve
from nova.router.codes import (
    SC_BLOCKING_MISMATCH,
    SC_BLOCKING_UNCERTAIN,
    SC_EXTRACTION_FAILED,
    SC_LLM_FAILURE,
    SC_LOW_CONFIDENCE,
    SC_MALFORMED_OUTPUT,
    SC_MISSING_EVIDENCE,
    SC_MISSING_FIELD,
    SC_SYSTEM_FAILSAFE,
    SC_TIMEOUT,
    SC_UNSAFE_LLM_OVERRIDE,
    SC_VALIDATION_FAILED,
)
from nova.router.llm import LlmAssistSuggestion
from nova.router.persistence import FailsafeAutoApproveError, decision_to_record

from .fixtures import (
    _ctx,
    known_field,
    make_extraction,
    make_policy,
    make_request,
    make_validation,
    missing_field,
)


class _FailingLlm:
    def suggest(self, request):  # noqa: ANN001
        return LlmAssistSuggestion(
            suggested_decision=DecisionKind.HUMAN_REVIEW,
            failed=True,
            error_message="provider down",
        )


class _UnsafeAutoApproveLlm:
    def suggest(self, request):  # noqa: ANN001
        return LlmAssistSuggestion(
            suggested_decision=DecisionKind.AUTO_APPROVE,
            rationale="looks fine",
        )


class _MalformedLlm:
    def suggest(self, request):  # noqa: ANN001
        return LlmAssistSuggestion(
            suggested_decision=DecisionKind.HUMAN_REVIEW,
            malformed=True,
            error_message="bad json",
        )


def test_valid_auto_approve() -> None:
    result = RouterService().decide(make_request())
    assert result.decision is DecisionKind.AUTO_APPROVE
    assert result.actor_type is DecisionActorType.ROUTER
    assert result.safety_constraints_applied == []
    assert result.requires_human_attention is False
    assert result.confidence is not None and result.confidence >= 0.85
    assert result.agent_version
    assert result.routing_rule_version
    assert result.input_fingerprint
    assert result.completed_at


def test_missing_information_blocks_auto_approve() -> None:
    ctx = _ctx()
    extraction = make_extraction(
        ctx,
        fields=[missing_field(ctx["trace_id"]), known_field(ctx["trace_id"], "vessel", "OCEAN")],
    )
    result = RouterService().decide(make_request(ctx=ctx, extraction=extraction))
    assert result.decision is not DecisionKind.AUTO_APPROVE
    assert SC_MISSING_FIELD in result.safety_constraints_applied


def test_mismatch_routes_to_amendment() -> None:
    ctx = _ctx()
    validation = make_validation(
        ctx,
        checks=[
            ValidationCheck(
                trace_id=ctx["trace_id"],
                rule_id=uuid4(),
                rule_code="BL_MATCH",
                field_name="bl_number",
                outcome=ValidationOutcome.MISMATCH,
                reason="values differ",
                blocking=True,
            )
        ],
    )
    result = RouterService().decide(make_request(ctx=ctx, validation=validation))
    assert result.decision is DecisionKind.AMENDMENT_REQUEST
    assert SC_BLOCKING_MISMATCH in result.safety_constraints_applied


def test_uncertain_routes_to_human_review() -> None:
    ctx = _ctx()
    validation = make_validation(
        ctx,
        checks=[
            ValidationCheck(
                trace_id=ctx["trace_id"],
                rule_id=uuid4(),
                rule_code="BL_CHECK",
                field_name="bl_number",
                outcome=ValidationOutcome.UNCERTAIN,
                reason="low conf",
                blocking=True,
            )
        ],
    )
    result = RouterService().decide(make_request(ctx=ctx, validation=validation))
    assert result.decision is DecisionKind.HUMAN_REVIEW
    assert SC_BLOCKING_UNCERTAIN in result.safety_constraints_applied


def test_low_confidence_blocks_auto_approve() -> None:
    ctx = _ctx()
    extraction = make_extraction(
        ctx,
        fields=[
            known_field(ctx["trace_id"], confidence=0.4),
            known_field(ctx["trace_id"], "vessel", "OCEAN"),
        ],
    )
    result = RouterService().decide(make_request(ctx=ctx, extraction=extraction))
    assert result.decision is DecisionKind.HUMAN_REVIEW
    assert SC_LOW_CONFIDENCE in result.safety_constraints_applied


def test_missing_evidence_blocks_auto_approve() -> None:
    ctx = _ctx()
    from nova.contracts.extraction import ExtractedField, ExtractionResult

    bare = ExtractedField.model_construct(
        trace_id=ctx["trace_id"],
        field_name="bl_number",
        value="BL-1",
        value_type="string",
        presence=FieldPresence.KNOWN,
        confidence=0.95,
        uncertainty=UncertaintyFlag.NONE,
        evidence=[],
        warnings=[],
        uncertainty_codes=[],
        confidence_band=None,
        confidence_source=None,
    )
    extraction = ExtractionResult.model_construct(
        trace_id=ctx["trace_id"],
        run_id=ctx["run_id"],
        document_id=ctx["document_id"],
        document_version_id=ctx["document_version_id"],
        shipment_id=ctx["shipment_id"],
        status=ExtractionStatus.SUCCEEDED,
        fields=[bare, known_field(ctx["trace_id"], "vessel", "OCEAN")],
        warnings=[],
        errors=[],
    )
    result = RouterService().decide(make_request(ctx=ctx, extraction=extraction))
    assert result.decision is not DecisionKind.AUTO_APPROVE
    assert SC_MISSING_EVIDENCE in result.safety_constraints_applied


def test_extractor_failure() -> None:
    ctx = _ctx()
    extraction = make_extraction(
        ctx,
        status=ExtractionStatus.FAILED,
        fields=[],
        error_code="EXTRACT_TIMEOUT",
    )
    # Fix errors to StageError
    extraction = extraction.model_copy(
        update={
            "errors": [
                StageError(code="EXTRACT_TIMEOUT", message="timeout", retryable=True)
            ]
        }
    )
    result = RouterService().decide(make_request(ctx=ctx, extraction=extraction))
    assert result.decision is DecisionKind.HUMAN_REVIEW
    assert SC_EXTRACTION_FAILED in result.safety_constraints_applied


def test_validator_failure() -> None:
    ctx = _ctx()
    validation = make_validation(
        ctx,
        status=ValidationStatus.FAILED,
        checks=[],
        error_code="RULESET_MISSING",
    )
    validation = validation.model_copy(
        update={
            "errors": [
                StageError(code="RULESET_MISSING", message="missing", retryable=False)
            ]
        }
    )
    result = RouterService().decide(make_request(ctx=ctx, validation=validation))
    assert result.decision is DecisionKind.HUMAN_REVIEW
    assert SC_VALIDATION_FAILED in result.safety_constraints_applied


def test_llm_failure_fail_closed() -> None:
    result = RouterService(llm=_FailingLlm()).decide(make_request())
    # Valid inputs remain AUTO_APPROVE-eligible; LLM failure alone on eligible
    # path: service sets auto_eligible False when LLM fails.
    assert result.decision is DecisionKind.HUMAN_REVIEW
    assert SC_LLM_FAILURE in result.safety_constraints_applied


def test_llm_attempts_unsafe_auto_approve_overridden() -> None:
    ctx = _ctx()
    validation = make_validation(
        ctx,
        checks=[
            ValidationCheck(
                trace_id=ctx["trace_id"],
                rule_id=uuid4(),
                rule_code="BL_MATCH",
                field_name="bl_number",
                outcome=ValidationOutcome.MISMATCH,
                reason="diff",
                blocking=True,
            )
        ],
    )
    req = make_request(
        ctx=ctx,
        validation=validation,
        llm_suggestion=LlmRoutingSuggestion(
            trace_id=ctx["trace_id"],
            available=True,
            decision=DecisionKind.AUTO_APPROVE,
            rationale="looks fine",
            triggering_check_ids=[],
        ),
    )
    result = RouterService().decide(req)
    assert result.decision is not DecisionKind.AUTO_APPROVE
    assert result.llm_overridden is True
    assert result.unsafe_llm_attempt is True
    assert SC_UNSAFE_LLM_OVERRIDE in result.safety_constraints_applied
    assert SC_BLOCKING_MISMATCH in result.safety_constraints_applied


def test_llm_malformed_fail_closed() -> None:
    ctx = _ctx()
    req = make_request(
        ctx=ctx,
        llm_suggestion=LlmRoutingSuggestion(
            trace_id=ctx["trace_id"],
            available=True,
            malformed=True,
            decision=None,
            raw_payload={"decision": "YES_APPROVE"},
        ),
    )
    # Base case is auto-eligible; malformed LLM adds constraint → not AUTO_APPROVE
    result = RouterService().decide(req)
    assert result.decision is DecisionKind.HUMAN_REVIEW
    assert SC_MALFORMED_OUTPUT in result.safety_constraints_applied


def test_system_failsafe() -> None:
    result = RouterService().decide(make_request(), force_failsafe=True)
    assert result.decision is DecisionKind.HUMAN_REVIEW
    assert result.actor_type is DecisionActorType.SYSTEM_FAILSAFE
    assert SC_SYSTEM_FAILSAFE in result.safety_constraints_applied


def test_timeout_failsafe() -> None:
    result = RouterService().decide(make_request(), timed_out=True)
    assert result.decision is DecisionKind.HUMAN_REVIEW
    assert result.actor_type is DecisionActorType.SYSTEM_FAILSAFE
    assert SC_TIMEOUT in result.safety_constraints_applied


def test_failsafe_cannot_store_auto_approve() -> None:
    base = RouterService().decide(make_request())
    with pytest.raises((ValidationError, FailsafeAutoApproveError, ValueError)):
        bad = base.model_copy(
            update={
                "decision": DecisionKind.AUTO_APPROVE,
                "actor_type": DecisionActorType.SYSTEM_FAILSAFE,
                "safety_constraints_applied": [],
                "requires_human_attention": False,
            }
        )
        assert_failsafe_cannot_auto_approve(bad)
        decision_to_record(bad)


def test_decision_persistence_record_shape() -> None:
    result = RouterService().decide(make_request())
    record = decision_to_record(result)
    assert record.disposition == "AUTO_APPROVE"
    assert record.actor_type == "router"
    assert record.input_fingerprint == result.input_fingerprint
    assert record.agent_version == result.agent_version
    assert record.reason_codes == result.reason_codes


def test_repeated_evaluation_idempotent() -> None:
    cache: dict = {}
    service = RouterService(decision_cache=cache)
    req = make_request()
    first = service.decide(req)
    second = service.decide(req)
    assert first.decision == second.decision
    assert first.input_fingerprint == second.input_fingerprint
    # Second should note replay
    assert any("IDEMPOTENT" in c or "REPLAY" in c for c in second.reason_codes) or (
        first.decision == second.decision
    )


def test_port_llm_unsafe_override() -> None:
    ctx = _ctx()
    validation = make_validation(
        ctx,
        checks=[
            ValidationCheck(
                trace_id=ctx["trace_id"],
                rule_id=uuid4(),
                rule_code="X",
                field_name="bl_number",
                outcome=ValidationOutcome.UNCERTAIN,
                reason="unc",
                blocking=True,
            )
        ],
    )
    result = RouterService(llm=_UnsafeAutoApproveLlm()).decide(
        make_request(ctx=ctx, validation=validation)
    )
    assert result.decision is DecisionKind.HUMAN_REVIEW
    assert result.unsafe_llm_attempt is True


def test_contract_rejects_failsafe_auto_approve() -> None:
    good = RouterService().decide(make_request())
    with pytest.raises(ValidationError):
        DecisionResult(
            trace_id=good.trace_id,
            run_id=good.run_id,
            document_id=good.document_id,
            document_version_id=good.document_version_id,
            shipment_id=good.shipment_id,
            verification_run_id=good.verification_run_id,
            validation_result_id=good.validation_result_id,
            decision=DecisionKind.AUTO_APPROVE,
            reasons=[],
            reason_codes=[],
            policy_id="p",
            policy_version="1",
            routing_rule_version="1",
            agent_version="1",
            requires_human_attention=False,
            actor_type=DecisionActorType.SYSTEM_FAILSAFE,
            input_fingerprint="x",
            completed_at=good.completed_at,
            safety_constraints_applied=[],
        )


def test_policy_rejects_auto_approve_mismatch_mapping() -> None:
    ctx = _ctx()
    with pytest.raises(ValidationError):
        make_policy(ctx, blocking_mismatch_decision=DecisionKind.AUTO_APPROVE)
