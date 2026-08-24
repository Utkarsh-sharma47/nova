"""Human-readable evaluation / dogfood reporting."""

from __future__ import annotations

from typing import Any

from nova.evaluation.extractor.scorer import CaseScore


def format_dogfood_case(score: CaseScore, *, document_preview: str = "") -> str:
    lines = [
        f"=== dogfood: {score.case_id} ({score.category}) ===",
        f"status: {'PASS' if score.passed else 'FAIL'} pred_status={score.pred_status}",
    ]
    if document_preview:
        preview = document_preview.strip().splitlines()[:8]
        lines.append("document preview:")
        lines.extend(f"  | {line}" for line in preview)
    lines.append("fields:")
    for name, detail in score.field_details.items():
        gold = detail.get("gold", {})
        pred = detail.get("pred", {})
        mark = "OK" if detail.get("error") is None and _field_ok(gold, pred) else "DIFF"
        lines.append(
            f"  [{mark}] {name}: gold={gold.get('presence')}/{gold.get('value')!r} "
            f"pred={pred.get('presence')}/{pred.get('value')!r} "
            f"evidence={pred.get('evidence_count', 0)}"
        )
    if score.failures:
        lines.append("failures:")
        lines.extend(f"  - {f}" for f in score.failures)
    return "\n".join(lines)


def _field_ok(gold: dict[str, Any], pred: dict[str, Any]) -> bool:
    if not pred:
        return False
    return gold.get("presence") == pred.get("presence") and gold.get("value") == pred.get(
        "value"
    )
