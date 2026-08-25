"""Extractor evaluation suite tests."""

from __future__ import annotations

from nova.evaluation.extractor import run_extractor_evaluation


def test_extractor_assignment_eval_gate() -> None:
    metrics, results = run_extractor_evaluation()
    assert metrics.n >= 2
    assert metrics.fabrication_count == 0
    assert metrics.gate_passed
    assert metrics.field_presence_accuracy == 1.0
    assert metrics.known_value_accuracy == 1.0
    assert {case["case_id"] for case in results} >= {
        "ext_assignment_clean_invoice",
        "ext_assignment_missing_fields",
    }
