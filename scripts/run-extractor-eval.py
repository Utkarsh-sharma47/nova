#!/usr/bin/env python3
"""Run the fixed Extractor evaluation / regression suite."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nova.evaluation.extractor.regression import (  # noqa: E402
    REGRESSION_POLICY_SUMMARY,
    apply_regression_gate,
)
from nova.evaluation.extractor.runner import (  # noqa: E402
    format_report,
    run_extractor_evaluation,
    write_report_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=ROOT / "fixtures" / "evaluation" / "extractor",
        help="Path to extractor evaluation fixtures root",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path to write machine-readable report JSON",
    )
    parser.add_argument(
        "--show-policy",
        action="store_true",
        help="Print regression policy summary and exit 0",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Less per-case field detail on failures",
    )
    args = parser.parse_args()

    if args.show_policy:
        print(REGRESSION_POLICY_SUMMARY)
        return 0

    result = run_extractor_evaluation(fixtures_root=args.fixtures)
    print(format_report(result, verbose=not args.quiet))
    gate = apply_regression_gate(result)
    print()
    print(gate.message)

    if args.json_out:
        write_report_json(result, args.json_out)
        print(f"wrote {args.json_out}")

    return 0 if gate.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
