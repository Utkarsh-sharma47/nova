#!/usr/bin/env python3
"""Run authoritative Part 1 AI evaluation suites and write reports.

Usage:
  PYTHONPATH=src python scripts/run_full_evaluation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nova.evaluation.decision import run_decision_evaluation  # noqa: E402
from nova.evaluation.extractor import run_extractor_evaluation, write_report as write_extractor_report  # noqa: E402
from nova.evaluation.validator.runner import run_dataset, write_report  # noqa: E402


def main() -> int:
    out_dir = ROOT / "docs" / "evaluation" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    decision = run_decision_evaluation()
    decision_path = out_dir / "decision-eval-latest.json"
    decision_path.write_text(json.dumps(decision.to_dict(), indent=2, default=str) + "\n")

    extractor_metrics, extractor_cases = run_extractor_evaluation()
    write_extractor_report(
        extractor_metrics,
        extractor_cases,
        out_dir / "extractor-eval-latest.json",
    )

    full = run_dataset(
        ROOT / "fixtures/evaluation/validator/cases",
        dataset_id="validator-eval",
        dataset_revision="2026-08-25.1",
    )
    regression = run_dataset(
        ROOT / "fixtures/evaluation/validator/regression",
        dataset_id="validator-regression",
        dataset_revision="2026-08-25.1",
    )
    write_report(full, out_dir / "validator-eval-latest.json")
    write_report(regression, out_dir / "validator-regression-latest.json")

    m = decision.metrics
    print("=== Decision evaluation ===")
    print(f"n={m.n} accuracy={m.decision_accuracy}")
    print(f"false_auto_approve_count={m.false_auto_approve_count}")
    print(f"false_auto_approve_rate={m.false_auto_approve_rate}")
    print(f"gate_passed={m.false_auto_approve_gate_passed}")
    print(f"wrote {decision_path}")

    print("=== Extractor evaluation ===")
    print(f"n={extractor_metrics.n} presence_acc={extractor_metrics.field_presence_accuracy:.3f}")
    print(f"known_value_acc={extractor_metrics.known_value_accuracy:.3f}")
    print(f"fabrication_count={extractor_metrics.fabrication_count}")
    print(f"gate_passed={extractor_metrics.gate_passed}")

    print("=== Validator evaluation ===")
    print(f"n={full.n} accuracy={full.validation_accuracy:.3f}")
    print(f"unsafe_match_count={full.unsafe_match_count}")
    print(f"blocking={full.blocking} reasons={full.blocking_reasons}")

    print("=== Validator regression ===")
    print(f"n={regression.n} accuracy={regression.validation_accuracy:.3f}")
    print(f"unsafe_match_count={regression.unsafe_match_count}")
    print(f"blocking={regression.blocking} reasons={regression.blocking_reasons}")

    if not m.false_auto_approve_gate_passed or m.false_auto_approve_count != 0:
        print("FAIL: false AUTO_APPROVE gate")
        return 1
    if not extractor_metrics.gate_passed or extractor_metrics.fabrication_count != 0:
        print("FAIL: extractor fabrication gate")
        return 1
    if full.blocking or regression.blocking:
        print("FAIL: validator blocking reasons present")
        return 1
    if full.unsafe_match_count or regression.unsafe_match_count:
        print("FAIL: unsafe MATCH detected")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
