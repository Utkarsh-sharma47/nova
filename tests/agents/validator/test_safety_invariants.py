"""Core safety invariant tests for the Validator."""

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
    ValidationStatus,
)
from nova.llm import MockLLM, scripted_error, scripted_json, scripted_text
from nova.llm.errors import LLMTimeoutError
from nova.validation_store import FailingValidationStore, InMemoryValidationStore


def _ids() -> dict[str, object]:
    return {
        "trace_id": uuid4(),
        "run_id": uuid4(),
        "document_id": uuid4(),
        "document_version_id": uuid4(),
        "shipment_id": uuid4(),
        "customer_id": uuid4(),
    }


def _known(name: str, value: object, *, confidence: float = 0.95) -> ExtractedField:
    return ExtractedField(
        trace_id=uuid4(),
        field_name=name,
        value=value,
        presence=FieldPresence.KNOWN,
        confidence=confidence,
        confidence_band=ConfidenceBand.HIGH,
        uncertainty=UncertaintyFlag.NONE,
        evidence=[
            Evidence(source_type=EvidenceSourceType.DOCUMENT_SPAN, snippet=str(value), page=1)
        ],
    )


def _request(
    fields: list[ExtractedField], rules: list[CustomerRuleSnapshot], **kwargs: object
) -> ValidationRequest:
    ids = _ids()
    return ValidationRequest(
        **ids,  # type: ignore[arg-type]
        extraction_result_id=uuid4(),
        rules=rules,
        extracted_fields=fields,
        **kwargs,  # type: ignore[arg-type]
    )


def test_deterministic_mismatch_cannot_become_match_via_llm() -> None:
    rule = CustomerRuleSnapshot(
        trace_id=uuid4(),
        rule_id=uuid4(),
        rule_code="SHIPPER_EQ",
        version="1",
        severity="HIGH",
        requires_judgment=True,
        expression={"op": "equals", "field": "shipper", "expected": "Acme"},
    )
    llm = MockLLM(
        behaviors=[scripted_json({"outcome": "MATCH", "reason": "override", "confidence": 0.99})]
    )
    agent = ValidatorAgent(llm=llm, store=InMemoryValidationStore())
    result = agent.validate(_request([_known("shipper", "Other")], [rule]))
    assert result.status is ValidationStatus.COMPLETED
    assert result.checks[0].outcome is ValidationOutcome.MISMATCH
    assert result.checks[0].deterministic is True
    assert llm.call_count == 0


def test_missing_evidence_cannot_be_treated_as_verified_match() -> None:
    field = ExtractedField(
        trace_id=uuid4(),
        field_name="shipper",
        value="Acme",
        presence=FieldPresence.KNOWN,
        confidence=0.9,
        confidence_band=ConfidenceBand.HIGH,
        uncertainty=UncertaintyFlag.NONE,
        evidence=[Evidence(source_type=EvidenceSourceType.NONE)],
    )
    rule = CustomerRuleSnapshot(
        trace_id=uuid4(),
        rule_id=uuid4(),
        rule_code="SHIPPER_EQ",
        version="1",
        severity="HIGH",
        expression={"op": "equals", "field": "shipper", "expected": "Acme"},
    )
    result = ValidatorAgent(store=InMemoryValidationStore()).validate(_request([field], [rule]))
    assert result.checks[0].outcome is ValidationOutcome.UNCERTAIN
    assert result.checks[0].reason == "MISSING_EVIDENCE"


def test_llm_failure_cannot_become_successful_validation() -> None:
    rule = CustomerRuleSnapshot(
        trace_id=uuid4(),
        rule_id=uuid4(),
        rule_code="JUDGE",
        version="1",
        severity="HIGH",
        requires_judgment=True,
        expression={"op": "judgment", "field": "commodity"},
    )
    llm = MockLLM(behaviors=[scripted_error(LLMTimeoutError("timeout"))])
    result = ValidatorAgent(llm=llm, store=InMemoryValidationStore()).validate(
        _request([_known("commodity", "steel")], [rule])
    )
    assert result.status is ValidationStatus.COMPLETED
    assert result.checks[0].outcome is ValidationOutcome.UNCERTAIN
    assert result.checks[0].reason == "LLM_FAILURE"
    assert result.match_count == 0


def test_malformed_llm_output_cannot_become_valid_match() -> None:
    rule = CustomerRuleSnapshot(
        trace_id=uuid4(),
        rule_id=uuid4(),
        rule_code="JUDGE",
        version="1",
        severity="HIGH",
        requires_judgment=True,
        expression={"op": "judgment", "field": "commodity"},
    )
    llm = MockLLM(behaviors=[scripted_text("<<<not-json>>>")])
    result = ValidatorAgent(llm=llm, store=InMemoryValidationStore(), max_llm_retries=0).validate(
        _request([_known("commodity", "steel")], [rule])
    )
    assert result.checks[0].outcome is ValidationOutcome.UNCERTAIN


def test_historical_validation_results_remain_auditable() -> None:
    store = InMemoryValidationStore()
    agent = ValidatorAgent(store=store)
    rule = CustomerRuleSnapshot(
        trace_id=uuid4(),
        rule_id=uuid4(),
        rule_code="BL_REQUIRED",
        version="1",
        severity="HIGH",
        expression={"op": "required", "field": "bl_number"},
    )
    agent.validate(_request([_known("bl_number", "BL-1")], [rule]))
    agent.validate(_request([_known("bl_number", "BL-2")], [rule]))
    records = store.list_all()
    assert len(records) == 2
    assert records[0].result.checks[0].actual_value == "BL-1"
    assert records[1].result.checks[0].actual_value == "BL-2"


def test_database_failure_marks_stage_failed() -> None:
    agent = ValidatorAgent(store=FailingValidationStore())
    rule = CustomerRuleSnapshot(
        trace_id=uuid4(),
        rule_id=uuid4(),
        rule_code="BL_REQUIRED",
        version="1",
        severity="HIGH",
        expression={"op": "required", "field": "bl_number"},
    )
    result = agent.validate(_request([_known("bl_number", "BL-1")], [rule]))
    assert result.status is ValidationStatus.FAILED
    assert result.error_code == "DATABASE_FAILURE"


def test_failed_extraction_cannot_succeed() -> None:
    agent = ValidatorAgent(store=InMemoryValidationStore())
    rule = CustomerRuleSnapshot(
        trace_id=uuid4(),
        rule_id=uuid4(),
        rule_code="BL_REQUIRED",
        version="1",
        severity="HIGH",
        expression={"op": "required", "field": "bl_number"},
    )
    result = agent.validate(
        _request([_known("bl_number", "BL-1")], [rule], extraction_status="FAILED")
    )
    assert result.status is ValidationStatus.FAILED
    assert result.error_code == "INVALID_EXTRACTION"
    assert result.checks == []
