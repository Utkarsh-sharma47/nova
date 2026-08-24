"""Load synthetic decision evaluation cases from fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from nova.contracts.common import (
    Evidence,
    EvidenceSourceType,
    FieldPresence,
    StageError,
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

DEFAULT_DATASET_DIR = (
    Path(__file__).resolve().parents[4] / "fixtures" / "evaluation" / "decision"
)


@dataclass(frozen=True)
class DecisionEvalCase:
    case_id: str
    category: str
    description: str
    gold_decision: DecisionKind
    must_not_auto_approve: bool
    tags: tuple[str, ...]
    request: RoutingRequest
    timed_out: bool = False
    force_failsafe: bool = False
    engine_error: str | None = None
    expect_unsafe_attempt: bool = False
    repeat_for_idempotency: bool = False


def dataset_dir() -> Path:
    return DEFAULT_DATASET_DIR


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    manifest_path = path or (dataset_dir() / "manifest.json")
    data: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    return data


def load_cases(
    *,
    tags: set[str] | None = None,
    categories: set[str] | None = None,
    dataset_root: Path | None = None,
) -> list[DecisionEvalCase]:
    root = dataset_root or dataset_dir()
    cases_path = root / "cases.jsonl"
    out: list[DecisionEvalCase] = []
    for line in cases_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        case_tags = tuple(raw.get("tags", []))
        if tags is not None and not tags.intersection(case_tags):
            continue
        if categories is not None and raw["category"] not in categories:
            continue
        out.append(_parse_case(raw))
    return out


def _uuid(value: str | None = None) -> UUID:
    return UUID(value) if value else UUID(int=0)


def _parse_case(raw: dict[str, Any]) -> DecisionEvalCase:
    ids = raw["ids"]
    trace_id = _uuid(ids["trace_id"])
    policy_raw = raw["policy"]
    policy = RoutingPolicySnapshot(
        trace_id=trace_id,
        policy_id=policy_raw.get("policy_id", "eval-default"),
        policy_version=policy_raw.get("policy_version", "1.0.0"),
        high_confidence_threshold=policy_raw.get("high_confidence_threshold", 0.85),
        low_confidence_threshold=policy_raw.get("low_confidence_threshold", 0.60),
        critical_fields=list(policy_raw.get("critical_fields", ["bl_number", "vessel"])),
        allow_auto_approve_on_unknown=policy_raw.get("allow_auto_approve_on_unknown", False),
        require_evidence_for_auto_approve=policy_raw.get(
            "require_evidence_for_auto_approve", True
        ),
    )

    fields = [_parse_field(f, trace_id) for f in raw["extraction"]["fields"]]
    extraction = ExtractionResult(
        trace_id=trace_id,
        run_id=_uuid(ids.get("run_id")),
        document_id=_uuid(ids["document_id"]),
        document_version_id=_uuid(ids["document_version_id"]),
        shipment_id=_uuid(ids["shipment_id"]),
        status=ExtractionStatus(raw["extraction"]["status"]),
        fields=fields,
        errors=[
            StageError(**e) for e in raw["extraction"].get("errors", [])
        ],
        error_code=raw["extraction"].get("error_code"),
        error_message=raw["extraction"].get("error_message"),
    )

    checks = [_parse_check(c, trace_id) for c in raw["validation"]["checks"]]
    validation = ValidationResult(
        trace_id=trace_id,
        document_id=_uuid(ids["document_id"]),
        document_version_id=_uuid(ids["document_version_id"]),
        shipment_id=_uuid(ids["shipment_id"]),
        status=ValidationStatus(raw["validation"].get("status", "COMPLETED")),
        checks=checks,
        match_count=raw["validation"].get(
            "match_count",
            sum(1 for c in checks if c.outcome == ValidationOutcome.MATCH),
        ),
        mismatch_count=raw["validation"].get(
            "mismatch_count",
            sum(1 for c in checks if c.outcome == ValidationOutcome.MISMATCH),
        ),
        uncertain_count=raw["validation"].get(
            "uncertain_count",
            sum(1 for c in checks if c.outcome == ValidationOutcome.UNCERTAIN),
        ),
        engine_version=raw["validation"].get("engine_version", "eval-1"),
        errors=[StageError(**e) for e in raw["validation"].get("errors", [])],
        error_code=raw["validation"].get("error_code"),
        error_message=raw["validation"].get("error_message"),
    )

    llm_suggestion = None
    if raw.get("llm_suggestion") is not None:
        ls = raw["llm_suggestion"]
        decision = ls.get("decision")
        llm_suggestion = LlmRoutingSuggestion(
            trace_id=trace_id,
            available=ls.get("available", True),
            malformed=ls.get("malformed", False),
            decision=DecisionKind(decision) if decision else None,
            rationale=ls.get("rationale"),
            triggering_check_ids=list(ls.get("triggering_check_ids", [])),
            evidence_refs=list(ls.get("evidence_refs", [])),
            fabricated_evidence=ls.get("fabricated_evidence", False),
            raw_payload=ls.get("raw_payload"),
        )

    request = RoutingRequest(
        trace_id=trace_id,
        run_id=_uuid(ids.get("run_id")),
        document_id=_uuid(ids["document_id"]),
        document_version_id=_uuid(ids["document_version_id"]),
        shipment_id=_uuid(ids["shipment_id"]),
        verification_run_id=_uuid(ids["verification_run_id"]),
        validation_result_id=_uuid(ids["validation_result_id"]),
        extraction=extraction,
        validation=validation,
        policy=policy,
        blocking_uncertainty_present=raw.get("blocking_uncertainty_present", False),
        correlation=raw.get("correlation"),
        llm_suggestion=llm_suggestion,
    )

    return DecisionEvalCase(
        case_id=raw["case_id"],
        category=raw["category"],
        description=raw.get("description", ""),
        gold_decision=DecisionKind(raw["gold_decision"]),
        must_not_auto_approve=bool(raw.get("must_not_auto_approve", False)),
        tags=tuple(raw.get("tags", [])),
        request=request,
        timed_out=bool(raw.get("timed_out", False)),
        force_failsafe=bool(raw.get("force_failsafe", False)),
        engine_error=raw.get("engine_error"),
        expect_unsafe_attempt=bool(raw.get("expect_unsafe_attempt", False)),
        repeat_for_idempotency=bool(raw.get("repeat_for_idempotency", False)),
    )


def _parse_field(raw: dict[str, Any], trace_id: UUID) -> ExtractedField:
    evidence = [
        Evidence(
            evidence_id=e.get("evidence_id"),
            source_type=EvidenceSourceType(e.get("source_type", "DOCUMENT_SPAN")),
            snippet=e.get("snippet"),
            page=e.get("page"),
        )
        for e in raw.get("evidence", [])
    ]
    return ExtractedField(
        trace_id=trace_id,
        field_name=raw["field_name"],
        value=raw.get("value"),
        presence=FieldPresence(raw["presence"]),
        confidence=raw.get("confidence"),
        uncertainty=UncertaintyFlag(raw.get("uncertainty", "NONE")),
        evidence=evidence,
    )


def _parse_check(raw: dict[str, Any], trace_id: UUID) -> ValidationCheck:
    return ValidationCheck(
        trace_id=trace_id,
        check_id=raw.get("check_id"),
        rule_id=_uuid(raw["rule_id"]),
        rule_code=raw["rule_code"],
        field_name=raw.get("field_name"),
        outcome=ValidationOutcome(raw["outcome"]),
        reason=raw.get("reason", ""),
        blocking=raw.get("blocking", True),
        severity=raw.get("severity", "BLOCKING"),
        confidence=raw.get("confidence"),
    )
