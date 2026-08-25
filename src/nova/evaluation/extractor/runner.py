"""Run extractor evaluation cases against MockLLM heuristic path."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from nova.contracts.common import DocumentContent
from nova.contracts.extraction import ExtractionRequest
from nova.evaluation.extractor.metrics import ExtractorEvalMetrics, compute_metrics
from nova.extraction.fields import ASSIGNMENT_FIELDS
from nova.extraction.heuristic import heuristic_extractor_response
from nova.extraction.service import ExtractorService
from nova.llm.mock import MockLLM

ROOT = Path(__file__).resolve().parents[4]


def run_extractor_evaluation(
    cases_dir: Path | None = None,
) -> tuple[ExtractorEvalMetrics, list[dict[str, Any]]]:
    path = cases_dir or (ROOT / "fixtures/evaluation/extractor/cases")
    cases = sorted(path.glob("*.json"))
    service = ExtractorService(MockLLM(factory=heuristic_extractor_response))
    results: list[dict[str, Any]] = []
    for case_path in cases:
        payload = json.loads(case_path.read_text(encoding="utf-8"))
        required = payload.get("required_fields") or list(ASSIGNMENT_FIELDS)
        result = service.extract(
                ExtractionRequest(
                trace_id=uuid4(),
                run_id=uuid4(),
                document_id=uuid4(),
                document_version_id=uuid4(),
                shipment_id=uuid4(),
                document_type=payload.get("document_type", "INVOICE"),
                content=DocumentContent(
                    media_type="text/plain",
                    text=payload["document_text"],
                    processor_name="passthrough_text",
                    processor_version="1.0.0",
                ),
                required_fields=required,
            )
        )
        actual_fields = {
            field.field_name: {
                "presence": field.presence.value,
                "value": field.value,
            }
            for field in result.fields
        }
        results.append(
            {
                "case_id": payload["case_id"],
                "expected_fields": payload["expected_fields"],
                "actual_fields": actual_fields,
                "status": result.status.value,
            }
        )
    return compute_metrics(results), results


def write_report(
    metrics: ExtractorEvalMetrics,
    results: list[dict[str, Any]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"metrics": metrics.to_dict(), "cases": results},
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
