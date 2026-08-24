#!/usr/bin/env python3
"""Run the Validator evaluation and regression suites; write measured reports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nova.evaluation.validator.runner import run_dataset, write_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        type=Path,
        default=ROOT / "fixtures/evaluation/validator/cases",
    )
    parser.add_argument(
        "--regression",
        type=Path,
        default=ROOT / "fixtures/evaluation/validator/regression",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "docs/evaluation/reports",
    )
    args = parser.parse_args()

    full = run_dataset(
        args.cases,
        dataset_id="validator-eval",
        dataset_revision="2026-08-25.1",
    )
    regression = run_dataset(
        args.regression,
        dataset_id="validator-regression",
        dataset_revision="2026-08-25.1",
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_report(full, args.out_dir / "validator-eval-latest.json")
    write_report(regression, args.out_dir / "validator-regression-latest.json")

    print("=== Validator evaluation suite ===")
    print(f"n={full.n} accuracy={full.validation_accuracy:.3f}")
    print(f"false_match_rate={full.false_match_rate:.3f}")
    print(f"false_mismatch_rate={full.false_mismatch_rate:.3f}")
    print(f"uncertainty_rate={full.uncertainty_rate:.3f}")
    print(f"deterministic_rule_coverage={full.deterministic_rule_coverage:.3f}")
    print(f"llm_assisted_validation_rate={full.llm_assisted_validation_rate:.3f}")
    print(f"mean_latency_ms={full.mean_latency_ms}")
    print(f"failure_rate={full.failure_rate:.3f}")
    print(f"unsafe_match_count={full.unsafe_match_count} rate={full.unsafe_match_rate:.3f}")
    print(f"blocking={full.blocking} reasons={full.blocking_reasons}")
    print()
    print("=== Validator regression suite ===")
    print(f"n={regression.n} accuracy={regression.validation_accuracy:.3f}")
    print(f"unsafe_match_count={regression.unsafe_match_count}")
    print(f"blocking={regression.blocking} reasons={regression.blocking_reasons}")
    print()
    print(f"Wrote {args.out_dir / 'validator-eval-latest.json'}")
    print(f"Wrote {args.out_dir / 'validator-regression-latest.json'}")

    if regression.unsafe_match_count > 0:
        print("FAIL: unsafe MATCH detected on regression set", file=sys.stderr)
        return 1
    if full.unsafe_match_count > 0:
        print("FAIL: unsafe MATCH detected on full eval set", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
