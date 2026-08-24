"""Regression gate for Extractor evaluation.

Rule: prompt / model / agent behavior changes → regression evaluation required.
A regression must be visible rather than silently accepted.
"""

from __future__ import annotations

from dataclasses import dataclass

from nova.evaluation.extractor.runner import EvalRunResult


@dataclass(frozen=True)
class RegressionGateResult:
    passed: bool
    blocking_failures: tuple[str, ...]
    message: str


def apply_regression_gate(result: EvalRunResult) -> RegressionGateResult:
    """Fail visibly when any fixed-regression case disagrees with gold.

    No invented numeric thresholds: the gate is exact gold agreement on the
    pinned regression dataset revision.
    """
    if result.passed:
        return RegressionGateResult(
            passed=True,
            blocking_failures=(),
            message=(
                f"Regression gate passed for {result.dataset_id}@"
                f"{result.dataset_revision}"
            ),
        )
    failures = tuple(
        f"{item['case_id']} ({item['category']}): " + "; ".join(item["failures"])
        for item in result.failures
    )
    return RegressionGateResult(
        passed=False,
        blocking_failures=failures,
        message=(
            "Regression gate FAILED — failures are visible and must be investigated "
            "before claiming prompt/model/agent improvement.\n"
            + "\n".join(f"  - {item}" for item in failures)
        ),
    )


REGRESSION_POLICY_SUMMARY = """
Extractor regression rule
-------------------------
Any change to Extractor prompts, models, decoding, post-processing, or agent
behavior that can alter ExtractionResult requires running the fixed Extractor
regression dataset (see fixtures/evaluation/extractor, revision pinned in
dataset.json).

- Regressions must fail the gate visibly (non-zero exit / report FAIL).
- Do not delete or weaken gold cases to obtain a green run.
- Do not invent statistical thresholds without measured baselines.
- Evaluation metrics ≠ production confidence scores.
""".strip()
