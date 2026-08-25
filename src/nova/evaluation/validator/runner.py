"""Validator evaluation runner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nova.agents.validator import ENGINE_VERSION, VALIDATOR_VERSION, ValidatorAgent
from nova.evaluation.validator.dataset import EvalCase, load_dataset
from nova.evaluation.validator.metrics import (
    CaseScore,
    ValidatorMetricsReport,
    aggregate_scores,
    score_case,
)


def run_case(case: EvalCase) -> tuple[CaseScore, Any]:
    agent = ValidatorAgent(llm=case.llm, store=case.store, persist=case.store is not None)
    result = agent.validate(case.request)
    score = score_case(
        case_id=case.case_id,
        category=case.category,
        gold_outcomes=case.gold_outcomes,
        result=result,
        gold_status=case.gold_status,
    )
    return score, result


def run_dataset(
    directory: Path,
    *,
    dataset_id: str,
    dataset_revision: str,
) -> ValidatorMetricsReport:
    cases = load_dataset(directory)
    scores: list[CaseScore] = []
    for case in cases:
        score, _ = run_case(case)
        scores.append(score)
    return aggregate_scores(
        scores,
        dataset_id=dataset_id,
        dataset_revision=dataset_revision,
        validator_version=VALIDATOR_VERSION,
        engine_version=ENGINE_VERSION,
    )


def write_report(report: ValidatorMetricsReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
