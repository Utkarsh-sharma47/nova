"""Deterministic Extractor evaluation suite (MockLLM + synthetic fixtures)."""

from __future__ import annotations

from pathlib import Path

import pytest

from nova.evaluation.extractor.dataset import DATASET_REVISION, load_extractor_dataset
from nova.evaluation.extractor.runner import (
    find_repo_root,
    format_report,
    run_extractor_evaluation,
)

REQUIRED_CATEGORIES = {
    "normal_document",
    "missing_fields",
    "ambiguous_values",
    "conflicting_values",
    "malformed_documents",
    "misleading_document_text",
    "prompt_injection_attempt",
    "fabricated_value_temptation",
    "low_confidence_extraction",
    "empty_document",
    "partial_information",
    "multiple_occurrences",
}


@pytest.fixture(scope="module")
def fixtures_root() -> Path:
    return find_repo_root() / "fixtures" / "evaluation" / "extractor"


def test_dataset_covers_required_categories(fixtures_root: Path) -> None:
    manifest, cases = load_extractor_dataset(fixtures_root)
    assert manifest["revision"] == DATASET_REVISION
    assert manifest.get("synthetic") is True
    categories = {case.category for case in cases}
    missing = REQUIRED_CATEGORIES - categories
    assert not missing, f"missing golden categories: {sorted(missing)}"
    assert len(cases) >= 12


def test_extractor_regression_suite_passes(fixtures_root: Path) -> None:
    result = run_extractor_evaluation(fixtures_root=fixtures_root, regression_only=True)
    report = format_report(result, verbose=True)
    assert result.passed, report
    assert result.metrics.n_cases >= 12
    assert result.metrics.schema_validity_rate == 1.0
    assert result.metrics.fabrication_rate == 0.0
    assert result.metrics.unsupported_field_rate == 0.0
    # Thresholds are not SLOs — assert only that rates were measured.
    assert result.metrics.field_extraction_accuracy is not None
    assert result.metrics.presence_classification_accuracy is not None
    assert result.metrics.latency_ms_mean is not None


def test_metrics_distinguish_eval_from_confidence(fixtures_root: Path) -> None:
    result = run_extractor_evaluation(fixtures_root=fixtures_root)
    notes = " ".join(result.metrics.notes).lower()
    assert "production confidence" in notes
    assert "evaluation" in notes or "gold" in notes
