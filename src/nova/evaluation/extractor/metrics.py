"""Extractor evaluation metrics (test/eval metrics — not production confidence)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ExtractorMetrics:
    """Aggregate metrics for an evaluation run.

    These are **test/evaluation metrics** derived from gold labels.
    They are distinct from per-field **production confidence** scores emitted
    by the Extractor at runtime.
    """

    n_cases: int = 0
    n_fields_scored: int = 0
    field_extraction_accuracy: float | None = None
    exact_match_rate: float | None = None
    presence_classification_accuracy: float | None = None
    evidence_availability_rate: float | None = None
    schema_validity_rate: float | None = None
    fabrication_rate: float | None = None
    unsupported_field_rate: float | None = None
    failure_rate: float | None = None
    latency_ms_p50: float | None = None
    latency_ms_p95: float | None = None
    latency_ms_mean: float | None = None
    cases_passed: int = 0
    cases_failed: int = 0
    slice_by_category: dict[str, dict[str, Any]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CaseMetricCounters:
    fields_total: int = 0
    field_value_correct: int = 0
    exact_match: int = 0
    presence_correct: int = 0
    evidence_ok: int = 0
    evidence_required: int = 0
    schema_valid: int = 0
    schema_checked: int = 0
    fabricated: int = 0
    fabrication_checked: int = 0
    unsupported_emitted: int = 0
    unsupported_checked: int = 0
    failed_status: int = 0
    status_checked: int = 0
    latency_ms: list[float] = field(default_factory=list)
    passed: bool = False
    category: str = ""


def _rate(numer: int, denom: int) -> float | None:
    if denom <= 0:
        return None
    return numer / denom


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * pct
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def aggregate_metrics(counters: list[CaseMetricCounters]) -> ExtractorMetrics:
    if not counters:
        return ExtractorMetrics(
            n_cases=0,
            notes=["empty evaluation run — no cases scored"],
        )

    fields_total = sum(c.fields_total for c in counters)
    metrics = ExtractorMetrics(
        n_cases=len(counters),
        n_fields_scored=fields_total,
        field_extraction_accuracy=_rate(
            sum(c.field_value_correct for c in counters), fields_total
        ),
        exact_match_rate=_rate(sum(c.exact_match for c in counters), fields_total),
        presence_classification_accuracy=_rate(
            sum(c.presence_correct for c in counters), fields_total
        ),
        evidence_availability_rate=_rate(
            sum(c.evidence_ok for c in counters),
            sum(c.evidence_required for c in counters),
        ),
        schema_validity_rate=_rate(
            sum(c.schema_valid for c in counters),
            sum(c.schema_checked for c in counters),
        ),
        fabrication_rate=_rate(
            sum(c.fabricated for c in counters),
            sum(c.fabrication_checked for c in counters),
        ),
        unsupported_field_rate=_rate(
            sum(c.unsupported_emitted for c in counters),
            sum(c.unsupported_checked for c in counters),
        ),
        failure_rate=_rate(
            sum(c.failed_status for c in counters),
            sum(c.status_checked for c in counters),
        ),
        cases_passed=sum(1 for c in counters if c.passed),
        cases_failed=sum(1 for c in counters if not c.passed),
        notes=[
            "Metrics are evaluation/test measurements against gold labels.",
            "Do not treat these rates as production confidence calibration.",
            "No statistically meaningful pass/fail threshold is asserted beyond gold agreement.",
        ],
    )

    latencies = [ms for c in counters for ms in c.latency_ms]
    if latencies:
        metrics.latency_ms_mean = sum(latencies) / len(latencies)
        metrics.latency_ms_p50 = _percentile(latencies, 0.50)
        metrics.latency_ms_p95 = _percentile(latencies, 0.95)

    by_cat: dict[str, list[CaseMetricCounters]] = {}
    for counter in counters:
        by_cat.setdefault(counter.category, []).append(counter)
    for category, group in sorted(by_cat.items()):
        metrics.slice_by_category[category] = {
            "n": len(group),
            "passed": sum(1 for c in group if c.passed),
            "failed": sum(1 for c in group if not c.passed),
            "field_extraction_accuracy": _rate(
                sum(c.field_value_correct for c in group),
                sum(c.fields_total for c in group),
            ),
            "presence_classification_accuracy": _rate(
                sum(c.presence_correct for c in group),
                sum(c.fields_total for c in group),
            ),
            "fabrication_rate": _rate(
                sum(c.fabricated for c in group),
                sum(c.fabrication_checked for c in group),
            ),
        }
    return metrics
