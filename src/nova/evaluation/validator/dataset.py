"""Validator evaluation case schema and loaders."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from nova.contracts.common import (
    ConfidenceBand,
    Evidence,
    EvidenceSourceType,
    FieldPresence,
    UncertaintyCode,
    UncertaintyFlag,
)
from nova.contracts.extraction import ExtractedField
from nova.contracts.validation import CustomerRuleSnapshot, ValidationRequest
from nova.llm import MockLLM, scripted_error, scripted_json, scripted_text
from nova.llm.errors import LLMMalformedOutputError, LLMProviderError, LLMTimeoutError
from nova.validation_store import FailingValidationStore, InMemoryValidationStore


@dataclass
class EvalCase:
    case_id: str
    category: str
    description: str
    request: ValidationRequest
    gold_outcomes: list[str]
    gold_status: str
    llm: MockLLM | None
    store: InMemoryValidationStore | FailingValidationStore | None
    expect_persist_failure: bool = False
    tags: list[str] | None = None


def _ids(raw: dict[str, Any] | None = None) -> dict[str, UUID]:
    raw = raw or {}
    return {
        "trace_id": UUID(raw["trace_id"]) if "trace_id" in raw else uuid4(),
        "run_id": UUID(raw["run_id"]) if "run_id" in raw else uuid4(),
        "document_id": UUID(raw["document_id"]) if "document_id" in raw else uuid4(),
        "document_version_id": UUID(raw["document_version_id"])
        if "document_version_id" in raw
        else uuid4(),
        "shipment_id": UUID(raw["shipment_id"]) if "shipment_id" in raw else uuid4(),
        "customer_id": UUID(raw["customer_id"]) if "customer_id" in raw else uuid4(),
    }


def _evidence(items: list[dict[str, Any]] | None, document_id: UUID) -> list[Evidence]:
    if not items:
        return []
    out: list[Evidence] = []
    for item in items:
        out.append(
            Evidence(
                evidence_id=item.get("evidence_id"),
                document_id=document_id,
                source_type=EvidenceSourceType(item.get("source_type", "DOCUMENT_SPAN")),
                snippet=item.get("snippet"),
                page=item.get("page", 1),
            )
        )
    return out


def _field(data: dict[str, Any], *, trace_id: UUID, document_id: UUID) -> ExtractedField:
    presence = FieldPresence(data.get("presence", "KNOWN"))
    uncertainty = UncertaintyFlag(data.get("uncertainty", "NONE"))
    codes_raw = data.get("uncertainty_codes") or (
        [UncertaintyCode.NONE.value] if presence is FieldPresence.KNOWN else []
    )
    return ExtractedField(
        trace_id=trace_id,
        document_id=document_id,
        field_name=data["field_name"],
        value=data.get("value"),
        presence=presence,
        confidence=data.get("confidence"),
        confidence_band=ConfidenceBand(data.get("confidence_band", "UNKNOWN")),
        uncertainty=uncertainty,
        uncertainty_codes=[UncertaintyCode(c) for c in codes_raw],
        evidence=_evidence(data.get("evidence"), document_id),
        candidates=data.get("candidates"),
        warnings=data.get("warnings") or [],
    )


def _rule(data: dict[str, Any], *, trace_id: UUID) -> CustomerRuleSnapshot:
    return CustomerRuleSnapshot(
        trace_id=trace_id,
        rule_id=UUID(data["rule_id"]) if "rule_id" in data else uuid4(),
        rule_code=data["rule_code"],
        version=str(data.get("version", "1")),
        severity=str(data.get("severity", "HIGH")),
        blocking=bool(data.get("blocking", True)),
        requires_judgment=bool(data.get("requires_judgment", False)),
        expression=dict(data.get("expression") or {}),
    )


def _build_llm(spec: dict[str, Any] | None) -> MockLLM | None:
    if not spec:
        return None
    mode = spec.get("mode", "response")
    if mode == "timeout":
        return MockLLM(behaviors=[scripted_error(LLMTimeoutError("Mock LLM timed out"))])
    if mode == "provider_error":
        return MockLLM(behaviors=[scripted_error(LLMProviderError("provider down"))])
    if mode == "malformed":
        return MockLLM(behaviors=[scripted_text(str(spec.get("response", "NOT_JSON{{")))])
    if mode == "scripted":
        behaviors = []
        for item in spec.get("scripted") or []:
            if isinstance(item, dict) and item.get("__error__") == "timeout":
                behaviors.append(scripted_error(LLMTimeoutError("timeout")))
            elif isinstance(item, dict) and item.get("__error__") == "malformed":
                behaviors.append(scripted_error(LLMMalformedOutputError("bad")))
            elif isinstance(item, dict):
                behaviors.append(scripted_json(item))
            else:
                behaviors.append(scripted_text(str(item)))
        return MockLLM(behaviors=behaviors)
    response = spec.get("response")
    if isinstance(response, dict):
        return MockLLM(behaviors=[scripted_json(response)])
    if response is not None:
        return MockLLM(behaviors=[scripted_text(str(response))])
    return MockLLM(default_content={"outcome": "UNCERTAIN", "reason": "default", "confidence": 0.0})


def load_case(path: Path) -> EvalCase:
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = _ids(data.get("ids"))
    fields = [
        _field(f, trace_id=ids["trace_id"], document_id=ids["document_id"])
        for f in data.get("extracted_fields") or []
    ]
    rules = [_rule(r, trace_id=ids["trace_id"]) for r in data.get("rules") or []]
    request = ValidationRequest(
        **ids,
        extraction_result_id=UUID(data["extraction_result_id"])
        if "extraction_result_id" in data
        else uuid4(),
        ruleset_id=data.get("ruleset_id", "eval-rules"),
        ruleset_version=data.get("ruleset_version", "1.0.0"),
        rules=rules,
        extracted_fields=fields,
        timeout_ms=int(data.get("timeout_ms", 30_000)),
        extraction_status=data.get("extraction_status"),
    )
    store_spec = data.get("store") or {"type": "memory"}
    store: InMemoryValidationStore | FailingValidationStore | None
    if store_spec.get("type") == "failing":
        store = FailingValidationStore()
    elif store_spec.get("type") == "none":
        store = None
    else:
        store = InMemoryValidationStore()

    return EvalCase(
        case_id=data["case_id"],
        category=data.get("category", "uncategorized"),
        description=data.get("description", ""),
        request=request,
        gold_outcomes=list(data.get("gold_outcomes") or []),
        gold_status=str(data.get("gold_status", "COMPLETED")),
        llm=_build_llm(data.get("llm")),
        store=store,
        expect_persist_failure=bool(data.get("expect_persist_failure", False)),
        tags=list(data.get("tags") or []),
    )


def load_dataset(directory: Path) -> list[EvalCase]:
    paths = sorted(directory.glob("*.json"))
    return [load_case(p) for p in paths if p.name != "manifest.json"]
