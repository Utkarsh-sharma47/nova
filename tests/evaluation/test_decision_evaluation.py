"""Router decision evaluation suite — false AUTO_APPROVE gate."""

from __future__ import annotations

import json

from nova.evaluation.decision.runner import run_decision_evaluation


def test_decision_evaluation_zero_false_auto_approve() -> None:
    report = run_decision_evaluation()
    assert report.metrics.n >= 10
    assert report.metrics.false_auto_approve_count == 0
    assert report.metrics.false_auto_approve_gate_passed is True
    assert report.failures == ()


def test_decision_evaluation_metrics_artifact() -> None:
    report = run_decision_evaluation()
    artifact = json.dumps(report.to_dict(), indent=2, default=str)
    assert "false_auto_approve_rate" in artifact
    assert report.metrics.decision_accuracy == 1.0
