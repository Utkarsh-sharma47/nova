"""Extractor evaluation harness (deterministic, fixture-driven)."""

from nova.evaluation.extractor.dataset import (
    DATASET_ID,
    DATASET_REVISION,
    load_extractor_dataset,
)
from nova.evaluation.extractor.metrics import ExtractorMetrics, aggregate_metrics
from nova.evaluation.extractor.runner import (
    EvalRunResult,
    format_report,
    run_extractor_evaluation,
)
from nova.evaluation.extractor.scorer import CaseScore, score_case

__all__ = [
    "DATASET_ID",
    "DATASET_REVISION",
    "CaseScore",
    "EvalRunResult",
    "ExtractorMetrics",
    "aggregate_metrics",
    "format_report",
    "load_extractor_dataset",
    "run_extractor_evaluation",
    "score_case",
]
