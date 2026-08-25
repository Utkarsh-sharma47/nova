"""Validator failure-injection tests."""

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
from nova.llm import MockLLM, scripted_error, scripted_json
from nova.llm.errors import LLMProviderError
from nova.validation_store import InMemoryValidationStore


def _known(name: str, value: object) -> ExtractedField:
    return ExtractedField(
        trace_id=uuid4(),
        field_name=name,
        value=value,
        presence=FieldPresence.KNOWN,
        confidence=0.9,
        confidence_band=ConfidenceBand.HIGH,
        uncertainty=UncertaintyFlag.NONE,
        evidence=[
            Evidence(source_type=EvidenceSourceType.DOCUMENT_SPAN, snippet=str(value), page=1)
        ],
    )


def _req(fields: list[ExtractedField], rules: list[CustomerRuleSnapshot]) -> ValidationRequest:
    return ValidationRequest(
        trace_id=uuid4(),
        run_id=uuid4(),
        document_id=uuid4(),
        document_version_id=uuid4(),
        shipment_id=uuid4(),
        customer_id=uuid4(),
        extraction_result_id=uuid4(),
        rules=rules,
        extracted_fields=fields,
    )


def test_llm_provider_failure_is_uncertain() -> None:
    rule = CustomerRuleSnapshot(
        trace_id=uuid4(),
        rule_id=uuid4(),
        rule_code="J",
        version="1",
        severity="HIGH",
        requires_judgment=True,
        expression={"op": "judgment", "field": "commodity"},
    )
    llm = MockLLM(behaviors=[scripted_error(LLMProviderError("down"))])
    result = ValidatorAgent(llm=llm, store=InMemoryValidationStore(), max_llm_retries=0).validate(
        _req([_known("commodity", "x")], [rule])
    )
    assert result.checks[0].outcome is ValidationOutcome.UNCERTAIN
    assert result.status is ValidationStatus.COMPLETED


def test_llm_illegal_outcome_rejected() -> None:
    rule = CustomerRuleSnapshot(
        trace_id=uuid4(),
        rule_id=uuid4(),
        rule_code="J",
        version="1",
        severity="HIGH",
        requires_judgment=True,
        expression={"op": "judgment", "field": "commodity"},
    )
    llm = MockLLM(
        behaviors=[
            scripted_json({"outcome": "AUTO_APPROVE", "reason": "nope", "confidence": 1.0})
        ]
    )
    result = ValidatorAgent(llm=llm, store=InMemoryValidationStore(), max_llm_retries=0).validate(
        _req([_known("commodity", "x")], [rule])
    )
    assert result.checks[0].outcome is ValidationOutcome.UNCERTAIN
