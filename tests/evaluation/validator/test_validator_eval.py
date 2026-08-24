"""Validator evaluation harness and regression suite tests."""

from __future__ import annotations

from pathlib import Path

from nova.evaluation.validator.runner import run_dataset

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "evaluation" / "validator"


def test_full_eval_suite_runs_without_unsafe_match() -> None:
    report = run_dataset(
        FIXTURES / "cases",
        dataset_id="validator-eval",
        dataset_revision="2026-08-25.1",
    )
    assert report.n >= 16
    assert report.unsafe_match_count == 0
    assert report.validation_accuracy > 0.0


def test_regression_suite_blocks_unsafe_match() -> None:
    report = run_dataset(
        FIXTURES / "regression",
        dataset_id="validator-regression",
        dataset_revision="2026-08-25.1",
    )
    assert report.n >= 10
    assert report.unsafe_match_count == 0
    assert report.blocking is False


def test_metrics_cover_required_fields() -> None:
    report = run_dataset(
        FIXTURES / "cases",
        dataset_id="validator-eval",
        dataset_revision="2026-08-25.1",
    )
    d = report.to_dict()["metrics"]
    for key in (
        "validation_accuracy",
        "false_match_rate",
        "false_mismatch_rate",
        "uncertainty_rate",
        "deterministic_rule_coverage",
        "llm_assisted_validation_rate",
        "mean_latency_ms",
        "failure_rate",
        "unsafe_match_rate",
    ):
        assert key in d
