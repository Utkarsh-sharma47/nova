"""Deterministic Extractor evaluation runner (MockLLM, no network)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from nova.contracts.common import DocumentContent
from nova.contracts.extraction import ExtractionRequest
from nova.evaluation.extractor.dataset import (
    DATASET_ID,
    DATASET_REVISION,
    ExtractorCase,
    load_extractor_dataset,
)
from nova.evaluation.extractor.metrics import (
    CaseMetricCounters,
    ExtractorMetrics,
    aggregate_metrics,
)
from nova.evaluation.extractor.scorer import CaseScore, score_case
from nova.extraction.prompts import PROMPT_ID, PROMPT_VERSION
from nova.extraction.service import AGENT_VERSION, ExtractorService
from nova.llm.errors import LLMProviderError, LLMTimeoutError
from nova.llm.mock import MockLLM

REPO_ROOT_MARKERS = ("pyproject.toml", "AGENTS.md")


@dataclass
class EvalRunResult:
    dataset_id: str
    dataset_revision: str
    prompt_id: str
    prompt_version: str
    agent_version: str
    provider: str
    model: str
    metrics: ExtractorMetrics
    case_scores: list[CaseScore] = field(default_factory=list)
    passed: bool = False
    failures: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_revision": self.dataset_revision,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "agent_version": self.agent_version,
            "provider": self.provider,
            "model": self.model,
            "passed": self.passed,
            "metrics": self.metrics.to_dict(),
            "failures": self.failures,
            "cases": [
                {
                    "case_id": score.case_id,
                    "category": score.category,
                    "passed": score.passed,
                    "pred_status": score.pred_status,
                    "failures": score.failures,
                    "field_details": score.field_details,
                }
                for score in self.case_scores
            ],
        }


def find_repo_root(start: Path | None = None) -> Path:
    cur = (start or Path.cwd()).resolve()
    for candidate in (cur, *cur.parents):
        if all((candidate / marker).exists() for marker in REPO_ROOT_MARKERS):
            return candidate
    return cur


def run_extractor_evaluation(
    *,
    fixtures_root: Path | None = None,
    categories: set[str] | None = None,
    regression_only: bool = True,
) -> EvalRunResult:
    """Run Extractor golden/regression suite with MockLLM scripted responses."""
    root = fixtures_root
    if root is None:
        root = find_repo_root() / "fixtures" / "evaluation" / "extractor"
    manifest, cases = load_extractor_dataset(root, categories=categories)
    if regression_only:
        cases = [case for case in cases if case.in_regression]

    scores: list[CaseScore] = []
    counters: list[CaseMetricCounters] = []
    failures: list[dict[str, Any]] = []

    for case in cases:
        score = _run_case(case)
        scores.append(score)
        counters.append(score.counters)
        if not score.passed:
            failures.append(
                {
                    "case_id": score.case_id,
                    "category": score.category,
                    "failures": score.failures,
                    "pred_status": score.pred_status,
                    "field_details": score.field_details,
                }
            )

    metrics = aggregate_metrics(counters)
    metrics.notes.append(
        f"dataset={manifest.get('dataset_id', DATASET_ID)}"
        f"@{manifest.get('revision', DATASET_REVISION)}"
    )
    metrics.notes.append(
        "Regression rule: prompt/model/agent behavior changes require re-running "
        "this fixed dataset; regressions must be visible (failed cases listed)."
    )

    return EvalRunResult(
        dataset_id=str(manifest.get("dataset_id", DATASET_ID)),
        dataset_revision=str(manifest.get("revision", DATASET_REVISION)),
        prompt_id=PROMPT_ID,
        prompt_version=PROMPT_VERSION,
        agent_version=AGENT_VERSION,
        provider="mock",
        model="mock-extractor-v1",
        metrics=metrics,
        case_scores=scores,
        passed=len(failures) == 0,
        failures=failures,
    )


def _run_case(case: ExtractorCase) -> CaseScore:
    llm = _mock_for_case(case)
    service = ExtractorService(llm)
    request = _request_for_case(case)
    started = time.perf_counter()
    result = service.extract(request)
    latency_ms = (time.perf_counter() - started) * 1000.0
    return score_case(case, result, latency_ms=latency_ms)


def _mock_for_case(case: ExtractorCase) -> MockLLM:
    if case.llm_error == "timeout":
        return MockLLM(
            responses=[
                LLMTimeoutError("simulated timeout"),
                LLMTimeoutError("simulated timeout"),
                LLMTimeoutError("simulated timeout"),
            ]
        )
    if case.llm_error == "provider":
        return MockLLM(
            responses=[
                LLMProviderError("simulated provider failure", retryable=True),
                LLMProviderError("simulated provider failure", retryable=True),
                LLMProviderError("simulated provider failure", retryable=True),
            ]
        )
    if case.llm_response is None:
        # Empty / unreadable documents never call the LLM.
        return MockLLM(responses=[])
    # Malformed cases may need multiple identical bad responses for retries.
    if case.category == "malformed_documents":
        return MockLLM(responses=[case.llm_response, case.llm_response, case.llm_response])
    return MockLLM(responses=[case.llm_response])


def _request_for_case(case: ExtractorCase) -> ExtractionRequest:
    doc_id = uuid4()
    version_id = uuid4()
    shipment_id = uuid4()
    run_id = uuid4()
    text = case.document_text
    content = DocumentContent(
        media_type="text/plain",
        text=text if text.strip() else None,
        page_texts=None,
        processor_name="eval-fixture",
        processor_version="1.0.0",
        warnings=[],
    )
    return ExtractionRequest(
        trace_id=run_id,
        run_id=run_id,
        document_id=doc_id,
        document_version_id=version_id,
        shipment_id=shipment_id,
        customer_id=uuid4(),
        document_type=case.document_type,
        content=content,
        required_fields=list(case.required_fields),
        timeout_ms=60_000,
    )


def format_report(result: EvalRunResult, *, verbose: bool = True) -> str:
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("Nova Extractor evaluation report")
    lines.append("=" * 72)
    lines.append(f"dataset:          {result.dataset_id}@{result.dataset_revision}")
    lines.append(f"prompt:           {result.prompt_id}/{result.prompt_version}")
    lines.append(f"agent_version:    {result.agent_version}")
    lines.append(f"provider/model:   {result.provider}/{result.model}")
    lines.append(f"overall:          {'PASS' if result.passed else 'FAIL'}")
    lines.append(f"cases:            {result.metrics.cases_passed}/{result.metrics.n_cases} passed")
    lines.append("-" * 72)
    lines.append("Evaluation metrics (not production confidence):")
    m = result.metrics
    for label, value in (
        ("field_extraction_accuracy", m.field_extraction_accuracy),
        ("exact_match_rate", m.exact_match_rate),
        ("presence_classification_accuracy", m.presence_classification_accuracy),
        ("evidence_availability_rate", m.evidence_availability_rate),
        ("schema_validity_rate", m.schema_validity_rate),
        ("fabrication_rate", m.fabrication_rate),
        ("unsupported_field_rate", m.unsupported_field_rate),
        ("failure_rate", m.failure_rate),
        ("latency_ms_p50", m.latency_ms_p50),
        ("latency_ms_p95", m.latency_ms_p95),
        ("latency_ms_mean", m.latency_ms_mean),
    ):
        lines.append(f"  {label}: {_fmt(value)}")
    lines.append("-" * 72)
    if result.failures:
        lines.append("FAILED CASES (inspect these):")
        for failure in result.failures:
            lines.append(f"  [{failure['category']}] {failure['case_id']}")
            for item in failure["failures"]:
                lines.append(f"    - {item}")
            if verbose and failure.get("field_details"):
                lines.append("    field_details:")
                lines.append(
                    "    "
                    + json.dumps(failure["field_details"], indent=2, default=str).replace(
                        "\n", "\n    "
                    )
                )
    else:
        lines.append("No failed cases.")
    lines.append("=" * 72)
    return "\n".join(lines)


def write_report_json(result: EvalRunResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2, default=str) + "\n", encoding="utf-8")


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float) and value <= 1.0:
        return f"{value:.4f}"
    return f"{value:.2f}"
