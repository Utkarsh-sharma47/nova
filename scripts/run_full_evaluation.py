#!/usr/bin/env python3
"""Run full Part 1 AI evaluation + regression gates (Phase 10).

Reproducible command for:
  - Validator evaluation + regression (unsafe MATCH gate)
  - Router decision evaluation (false AUTO_APPROVE gate)
  - Extractor fabrication contract checks (pytest subset)

Does not replace unit/integration/E2E suites. MockLLM only — not live provider quality.
Exit code 1 if any blocking safety gate fails.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nova.evaluation.decision.runner import run_decision_evaluation  # noqa: E402
from nova.evaluation.validator.runner import run_dataset, write_report  # noqa: E402


def _run_validator(out_dir: Path) -> int:
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
    out_dir.mkdir(parents=True, exist_ok=True)
    write_report(full, out_dir / "validator-eval-latest.json")
    write_report(regression, out_dir / "validator-regression-latest.json")

    print("=== Validator evaluation ===")
    print(f"n={full.n} accuracy={full.validation_accuracy:.3f}")
    print(f"unsafe_match_count={full.unsafe_match_count} rate={full.unsafe_match_rate:.3f}")
    print(f"blocking={full.blocking} reasons={full.blocking_reasons}")
    print("=== Validator regression ===")
    print(f"n={regression.n} unsafe_match_count={regression.unsafe_match_count}")
    print(f"blocking={regression.blocking} reasons={regression.blocking_reasons}")

    if full.unsafe_match_count > 0 or regression.unsafe_match_count > 0:
        print("FAIL: unsafe MATCH detected", file=sys.stderr)
        return 1
    return 0


def _run_decision(out_dir: Path) -> int:
    report = run_decision_evaluation()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "decision-eval-latest.json"
    path.write_text(json.dumps(report.to_dict(), indent=2, default=str), encoding="utf-8")

    print("=== Decision / Router evaluation ===")
    print(f"n={report.metrics.n}")
    print(f"false_auto_approve_count={report.metrics.false_auto_approve_count}")
    print(f"false_auto_approve_rate={report.metrics.false_auto_approve_rate:.3f}")
    print(f"decision_accuracy={report.metrics.decision_accuracy:.3f}")
    print(f"gate_passed={report.metrics.false_auto_approve_gate_passed}")
    print(f"Wrote {path}")

    if report.metrics.false_auto_approve_count != 0:
        print("FAIL: false AUTO_APPROVE detected", file=sys.stderr)
        return 1
    if not report.metrics.false_auto_approve_gate_passed:
        print("FAIL: false AUTO_APPROVE gate failed", file=sys.stderr)
        return 1
    if report.failures:
        print(f"FAIL: decision eval failures={report.failures}", file=sys.stderr)
        return 1
    return 0


def _run_extractor_fabrication_gate() -> int:
    """Run fixed extractor contract/unit tests that encode fabrication=0 invariants."""
    print("=== Extractor fabrication contract gate (pytest) ===")
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/contracts/test_schemas.py::test_extraction_rejects_fabricated_known_null",
        "tests/extraction/test_extractor_service.py::test_fabricated_evidence_rejected",
        "tests/extraction/test_extractor_service.py::test_missing_evidence_downgrades_known",
        "tests/extraction/test_extraction_security.py",
    ]
    completed = subprocess.run(cmd, cwd=ROOT, check=False)
    if completed.returncode != 0:
        print("FAIL: extractor fabrication gate", file=sys.stderr)
        return 1
    print("extractor fabrication gate: PASS (contract/unit assertions)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "docs/evaluation/reports",
    )
    parser.add_argument(
        "--skip-pytest-gates",
        action="store_true",
        help="Skip extractor fabrication pytest subset (validators/decision only).",
    )
    args = parser.parse_args()

    rc = 0
    rc |= _run_validator(args.out_dir)
    rc |= _run_decision(args.out_dir)
    if not args.skip_pytest_gates:
        rc |= _run_extractor_fabrication_gate()

    if rc == 0:
        print("\nFULL EVALUATION GATES: PASS")
    else:
        print("\nFULL EVALUATION GATES: FAIL", file=sys.stderr)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
