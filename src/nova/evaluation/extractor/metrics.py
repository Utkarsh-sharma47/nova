"""Extractor evaluation metrics for assignment field presence/value."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ExtractorEvalMetrics:
    n: int
    field_presence_accuracy: float
    known_value_accuracy: float
    fabrication_count: int
    gate_passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_metrics(case_results: list[dict[str, Any]]) -> ExtractorEvalMetrics:
    if not case_results:
        return ExtractorEvalMetrics(
            n=0,
            field_presence_accuracy=0.0,
            known_value_accuracy=0.0,
            fabrication_count=0,
            gate_passed=False,
        )
    presence_ok = 0
    presence_total = 0
    value_ok = 0
    value_total = 0
    fabrication = 0
    for case in case_results:
        for field_name, expected in case["expected_fields"].items():
            actual = case["actual_fields"].get(field_name) or {}
            presence_total += 1
            expected_presence = expected["presence"]
            actual_presence = actual.get("presence")
            if actual_presence == expected_presence:
                presence_ok += 1
            if expected_presence != "KNOWN" and actual.get("value") not in (None, ""):
                fabrication += 1
            if expected_presence == "KNOWN":
                value_total += 1
                if str(actual.get("value") or "") == str(expected.get("value") or ""):
                    value_ok += 1
    return ExtractorEvalMetrics(
        n=len(case_results),
        field_presence_accuracy=presence_ok / presence_total if presence_total else 0.0,
        known_value_accuracy=value_ok / value_total if value_total else 1.0,
        fabrication_count=fabrication,
        gate_passed=fabrication == 0,
    )
