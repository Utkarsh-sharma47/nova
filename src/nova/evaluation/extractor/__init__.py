"""Extractor evaluation subpackage."""

from nova.evaluation.extractor.dataset import (
    DATASET_ID,
    DATASET_REVISION,
    ExtractorCase,
    load_extractor_dataset,
)
from nova.evaluation.extractor.metrics import ExtractorMetrics, aggregate_metrics
from nova.evaluation.extractor.regression import (
    REGRESSION_POLICY_SUMMARY,
    RegressionGateResult,
    apply_regression_gate,
)
from nova.evaluation.extractor.runner import (
    EvalRunResult,
    format_report,
    run_extractor_evaluation,
)
from nova.evaluation.extractor.scorer import CaseScore, score_case

__all__ = [
    "DATASET_ID",
    "DATASET_REVISION",
    "REGRESSION_POLICY_SUMMARY",
    "CaseScore",
    "EvalRunResult",
    "ExtractorCase",
    "ExtractorMetrics",
    "RegressionGateResult",
    "aggregate_metrics",
    "apply_regression_gate",
    "format_report",
    "load_extractor_dataset",
    "run_extractor_evaluation",
    "score_case",
]
