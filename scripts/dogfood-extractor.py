#!/usr/bin/env python3
"""Dogfood the Extractor against synthetic fixtures (easy failure inspection)."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nova.evaluation.extractor.dataset import load_extractor_dataset  # noqa: E402
from nova.evaluation.extractor.report import format_dogfood_case  # noqa: E402
from nova.evaluation.extractor.runner import (  # noqa: E402
    _mock_for_case,
    _request_for_case,
)
from nova.evaluation.extractor.scorer import score_case  # noqa: E402
from nova.extraction.service import ExtractorService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=ROOT / "fixtures" / "evaluation" / "extractor",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=None,
        help="Optional case_id filter (repeatable)",
    )
    args = parser.parse_args()

    _, cases = load_extractor_dataset(args.fixtures)
    if args.case:
        wanted = set(args.case)
        cases = [c for c in cases if c.case_id in wanted]
        missing = wanted - {c.case_id for c in cases}
        if missing:
            print(f"unknown case ids: {sorted(missing)}", file=sys.stderr)
            return 2

    failed = 0
    for case in cases:
        llm = _mock_for_case(case)
        service = ExtractorService(llm)
        request = _request_for_case(case)
        started = time.perf_counter()
        result = service.extract(request)
        latency_ms = (time.perf_counter() - started) * 1000
        score = score_case(case, result, latency_ms=latency_ms)
        print(format_dogfood_case(score, document_preview=case.document_text))
        print(f"latency_ms={latency_ms:.2f}")
        print()
        if not score.passed:
            failed += 1

    print(f"dogfood complete: {len(cases) - failed}/{len(cases)} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
