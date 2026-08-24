"""Run Router decision evaluation against labeled synthetic cases."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from nova.contracts.routing import DecisionKind
from nova.evaluation.decision.cases import DecisionEvalCase, load_cases, load_manifest
from nova.evaluation.decision.metrics import (
    DecisionCaseOutcome,
    DecisionMetrics,
    compute_decision_metrics,
)
from nova.router.service import RouterService


@dataclass(frozen=True)
class DecisionEvalReport:
    dataset_id: str
    dataset_revision: str
    policy_engine_version: str
    agent_version: str
    metrics: DecisionMetrics
    outcomes: tuple[DecisionCaseOutcome, ...]
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_revision": self.dataset_revision,
            "policy_engine_version": self.policy_engine_version,
            "agent_version": self.agent_version,
            "metrics": asdict(self.metrics),
            "outcomes": [asdict(o) for o in self.outcomes],
            "failures": list(self.failures),
        }


def run_decision_evaluation(
    *,
    tags: set[str] | None = None,
    categories: set[str] | None = None,
    dataset_root: Path | None = None,
    router: RouterService | None = None,
    calibration_target_false_auto_approve_rate: float | None = None,
) -> DecisionEvalReport:
    manifest = load_manifest((dataset_root / "manifest.json") if dataset_root else None)
    target = (
        calibration_target_false_auto_approve_rate
        if calibration_target_false_auto_approve_rate is not None
        else float(manifest.get("calibration_target_false_auto_approve_rate", 0.0))
    )
    cases = load_cases(tags=tags, categories=categories, dataset_root=dataset_root)
    service = router or RouterService()
    outcomes: list[DecisionCaseOutcome] = []
    failures: list[str] = []

    for case in cases:
        outcomes.extend(_run_case(service, case, failures))

    metrics = compute_decision_metrics(
        outcomes,
        calibration_target_false_auto_approve_rate=target,
    )
    return DecisionEvalReport(
        dataset_id=str(manifest.get("dataset_id", "decision-eval")),
        dataset_revision=str(manifest.get("revision", "unknown")),
        policy_engine_version=str(manifest.get("policy_engine_version", "")),
        agent_version=str(manifest.get("agent_version", "")),
        metrics=metrics,
        outcomes=tuple(outcomes),
        failures=tuple(failures),
    )


def _run_case(
    service: RouterService,
    case: DecisionEvalCase,
    failures: list[str],
) -> list[DecisionCaseOutcome]:
    runs = 2 if case.repeat_for_idempotency else 1
    results: list[DecisionCaseOutcome] = []
    prior_decision: DecisionKind | None = None

    for i in range(runs):
        failed = False
        try:
            result = service.decide(
                case.request,
                timed_out=case.timed_out,
                force_failsafe=case.force_failsafe,
                engine_error=case.engine_error,
            )
            predicted = result.decision
            unsafe = result.unsafe_llm_attempt
            latency = float(result.usage.latency_ms or 0) if result.usage else 0.0
            if case.expect_unsafe_attempt and not unsafe and i == 0:
                failures.append(
                    f"{case.case_id}: expected unsafe_llm_attempt to be recorded"
                )
            if case.must_not_auto_approve and predicted == DecisionKind.AUTO_APPROVE:
                failures.append(f"{case.case_id}: false AUTO_APPROVE")
            if prior_decision is not None and predicted != prior_decision:
                failures.append(
                    f"{case.case_id}: non-idempotent decision {prior_decision} -> {predicted}"
                )
                failed = True
            prior_decision = predicted
            # Gold check for second idempotent run uses same gold.
            gold = case.gold_decision
            results.append(
                DecisionCaseOutcome(
                    case_id=f"{case.case_id}#{i + 1}" if runs > 1 else case.case_id,
                    gold=gold,
                    predicted=predicted,
                    must_not_auto_approve=case.must_not_auto_approve,
                    unsafe_llm_attempt=unsafe,
                    latency_ms=latency,
                    failed=failed,
                )
            )
        except Exception as exc:  # noqa: BLE001 — eval harness records failures
            failures.append(f"{case.case_id}: exception {exc}")
            results.append(
                DecisionCaseOutcome(
                    case_id=case.case_id,
                    gold=case.gold_decision,
                    predicted=DecisionKind.HUMAN_REVIEW,
                    must_not_auto_approve=case.must_not_auto_approve,
                    unsafe_llm_attempt=False,
                    latency_ms=0.0,
                    failed=True,
                )
            )
    return results
