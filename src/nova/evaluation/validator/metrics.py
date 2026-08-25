"""Validator evaluation metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nova.contracts.validation import ValidationOutcome, ValidationResult, ValidationStatus


@dataclass
class CaseScore:
    case_id: str
    category: str
    gold_outcomes: list[str]
    pred_outcomes: list[str]
    agreement: bool
    unsafe_match: bool
    false_match: bool
    false_mismatch: bool
    uncertain: bool
    deterministic_checks: int
    llm_checks: int
    latency_ms: int | None
    failed: bool
    notes: str = ""


@dataclass
class ValidatorMetricsReport:
    dataset_id: str
    dataset_revision: str
    validator_version: str
    engine_version: str
    n: int
    validation_accuracy: float
    false_match_rate: float
    false_mismatch_rate: float
    uncertainty_rate: float
    deterministic_rule_coverage: float
    llm_assisted_validation_rate: float
    mean_latency_ms: float | None
    failure_rate: float
    unsafe_match_count: int
    unsafe_match_rate: float
    cases: list[CaseScore] = field(default_factory=list)
    blocking: bool = False
    blocking_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_revision": self.dataset_revision,
            "validator_version": self.validator_version,
            "engine_version": self.engine_version,
            "n": self.n,
            "metrics": {
                "validation_accuracy": self.validation_accuracy,
                "false_match_rate": self.false_match_rate,
                "false_mismatch_rate": self.false_mismatch_rate,
                "uncertainty_rate": self.uncertainty_rate,
                "deterministic_rule_coverage": self.deterministic_rule_coverage,
                "llm_assisted_validation_rate": self.llm_assisted_validation_rate,
                "mean_latency_ms": self.mean_latency_ms,
                "failure_rate": self.failure_rate,
                "unsafe_match_count": self.unsafe_match_count,
                "unsafe_match_rate": self.unsafe_match_rate,
            },
            "blocking": self.blocking,
            "blocking_reasons": self.blocking_reasons,
            "cases": [c.__dict__ for c in self.cases],
        }


def score_case(
    *,
    case_id: str,
    category: str,
    gold_outcomes: list[str],
    result: ValidationResult,
    gold_status: str | None = None,
) -> CaseScore:
    pred = [c.outcome.value for c in result.checks]
    # Align lengths: compare by position when counts match; else disagreement
    agreement = pred == gold_outcomes
    if gold_status is not None:
        agreement = agreement and (result.status.value == gold_status)

    false_match = False
    false_mismatch = False
    unsafe_match = False
    for gold, check in zip(gold_outcomes, result.checks, strict=False):
        if check.outcome is ValidationOutcome.MATCH and gold != ValidationOutcome.MATCH.value:
            false_match = True
            if gold in {ValidationOutcome.MISMATCH.value, ValidationOutcome.UNCERTAIN.value}:
                unsafe_match = True
        if check.outcome is ValidationOutcome.MISMATCH and gold == ValidationOutcome.MATCH.value:
            false_mismatch = True

    # Stage FAILED while gold expected COMPLETED with only MATCH is also unsafe if any MATCH claimed
    if result.status is ValidationStatus.FAILED and any(
        o == ValidationOutcome.MATCH.value for o in gold_outcomes
    ):
        # failure itself is not unsafe MATCH
        pass

    det = sum(1 for c in result.checks if c.deterministic)
    llm = sum(1 for c in result.checks if not c.deterministic)
    uncertain = any(c.outcome is ValidationOutcome.UNCERTAIN for c in result.checks) or (
        result.status is ValidationStatus.FAILED
    )

    return CaseScore(
        case_id=case_id,
        category=category,
        gold_outcomes=gold_outcomes,
        pred_outcomes=pred,
        agreement=agreement,
        unsafe_match=unsafe_match,
        false_match=false_match,
        false_mismatch=false_mismatch,
        uncertain=uncertain,
        deterministic_checks=det,
        llm_checks=llm,
        latency_ms=result.usage.latency_ms if result.usage else None,
        failed=result.status is ValidationStatus.FAILED,
    )


def aggregate_scores(
    scores: list[CaseScore],
    *,
    dataset_id: str,
    dataset_revision: str,
    validator_version: str,
    engine_version: str,
) -> ValidatorMetricsReport:
    n = len(scores)
    if n == 0:
        return ValidatorMetricsReport(
            dataset_id=dataset_id,
            dataset_revision=dataset_revision,
            validator_version=validator_version,
            engine_version=engine_version,
            n=0,
            validation_accuracy=0.0,
            false_match_rate=0.0,
            false_mismatch_rate=0.0,
            uncertainty_rate=0.0,
            deterministic_rule_coverage=0.0,
            llm_assisted_validation_rate=0.0,
            mean_latency_ms=None,
            failure_rate=0.0,
            unsafe_match_count=0,
            unsafe_match_rate=0.0,
            blocking=True,
            blocking_reasons=["empty_dataset"],
        )

    accuracy = sum(1 for s in scores if s.agreement) / n
    false_match_rate = sum(1 for s in scores if s.false_match) / n
    false_mismatch_rate = sum(1 for s in scores if s.false_mismatch) / n
    uncertainty_rate = sum(1 for s in scores if s.uncertain) / n
    total_checks = sum(s.deterministic_checks + s.llm_checks for s in scores) or 1
    det_cov = sum(s.deterministic_checks for s in scores) / total_checks
    llm_rate = sum(1 for s in scores if s.llm_checks > 0) / n
    latencies = [s.latency_ms for s in scores if s.latency_ms is not None]
    mean_lat = sum(latencies) / len(latencies) if latencies else None
    failure_rate = sum(1 for s in scores if s.failed) / n
    unsafe_count = sum(1 for s in scores if s.unsafe_match)
    unsafe_rate = unsafe_count / n

    blocking_reasons: list[str] = []
    if unsafe_count > 0:
        blocking_reasons.append(f"unsafe_match_count={unsafe_count}")

    return ValidatorMetricsReport(
        dataset_id=dataset_id,
        dataset_revision=dataset_revision,
        validator_version=validator_version,
        engine_version=engine_version,
        n=n,
        validation_accuracy=accuracy,
        false_match_rate=false_match_rate,
        false_mismatch_rate=false_mismatch_rate,
        uncertainty_rate=uncertainty_rate,
        deterministic_rule_coverage=det_cov,
        llm_assisted_validation_rate=llm_rate,
        mean_latency_ms=mean_lat,
        failure_rate=failure_rate,
        unsafe_match_count=unsafe_count,
        unsafe_match_rate=unsafe_rate,
        cases=scores,
        blocking=bool(blocking_reasons),
        blocking_reasons=blocking_reasons,
    )
