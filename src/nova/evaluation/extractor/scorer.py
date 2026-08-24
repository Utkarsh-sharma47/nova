"""Score a single Extractor evaluation case against gold labels."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from nova.contracts.common import FieldPresence
from nova.contracts.extraction import ExtractedField, ExtractionResult, ExtractionStatus
from nova.evaluation.extractor.dataset import ExtractorCase, GoldField
from nova.evaluation.extractor.metrics import CaseMetricCounters
from nova.extraction.fields import is_supported_field

_WS = re.compile(r"\s+")


@dataclass
class CaseScore:
    case_id: str
    category: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    counters: CaseMetricCounters = field(default_factory=CaseMetricCounters)
    pred_status: str | None = None
    field_details: dict[str, dict[str, Any]] = field(default_factory=dict)


def score_case(
    case: ExtractorCase,
    result: ExtractionResult,
    *,
    latency_ms: float | None = None,
) -> CaseScore:
    failures: list[str] = []
    counters = CaseMetricCounters(category=case.category)
    if latency_ms is not None:
        counters.latency_ms.append(latency_ms)

    counters.status_checked = 1
    pred_status = result.status.value
    if result.status == ExtractionStatus.FAILED:
        counters.failed_status = 1
    if pred_status not in case.expected_status:
        failures.append(
            f"status={pred_status} not in expected {list(case.expected_status)}"
        )

    counters.schema_checked = 1
    schema_ok = _schema_valid(result)
    if schema_ok:
        counters.schema_valid = 1
    elif case.expect_schema_valid:
        failures.append("result failed schema/invariant checks")

    by_name = {f.field_name: f for f in result.fields}

    # Unsupported field emissions (pred fields outside catalog).
    counters.unsupported_checked = 1
    unsupported = [name for name in by_name if not is_supported_field(name)]
    if unsupported:
        counters.unsupported_emitted = 1
        if not case.unsupported_fields_allowed:
            failures.append(f"unsupported fields emitted: {unsupported}")

    field_details: dict[str, dict[str, Any]] = {}
    for name, gold in case.gold_fields.items():
        counters.fields_total += 1
        pred = by_name.get(name)
        detail: dict[str, Any] = {"gold": _gold_dict(gold)}
        if pred is None:
            failures.append(f"missing field in result: {name}")
            detail["error"] = "missing"
            field_details[name] = detail
            continue

        detail["pred"] = {
            "presence": pred.presence.value,
            "value": pred.value,
            "confidence": pred.confidence,
            "uncertainty": pred.uncertainty.value,
            "evidence_count": len(pred.evidence),
        }

        presence_ok = pred.presence.value == gold.presence
        if presence_ok:
            counters.presence_correct += 1
        else:
            failures.append(
                f"{name}: presence pred={pred.presence.value} gold={gold.presence}"
            )

        value_ok = _values_equal(pred.value, gold.value, presence=gold.presence)
        if value_ok:
            counters.field_value_correct += 1
        else:
            failures.append(
                f"{name}: value pred={pred.value!r} gold={gold.value!r}"
            )

        if presence_ok and value_ok:
            counters.exact_match += 1

        if gold.require_evidence:
            counters.evidence_required += 1
            if pred.presence == FieldPresence.KNOWN and pred.evidence:
                counters.evidence_ok += 1
            else:
                failures.append(f"{name}: evidence required but missing/invalid")

        if gold.max_confidence is not None and pred.confidence is not None:
            if pred.confidence > gold.max_confidence:
                failures.append(
                    f"{name}: confidence {pred.confidence} > max {gold.max_confidence}"
                )
        if gold.min_confidence is not None and pred.confidence is not None:
            if pred.confidence < gold.min_confidence:
                failures.append(
                    f"{name}: confidence {pred.confidence} < min {gold.min_confidence}"
                )
        if gold.uncertainty_in is not None:
            if pred.uncertainty.value not in gold.uncertainty_in:
                failures.append(
                    f"{name}: uncertainty {pred.uncertainty.value} "
                    f"not in {list(gold.uncertainty_in)}"
                )

        # Fabrication: KNOWN value not grounded in document text.
        counters.fabrication_checked += 1
        fabricated = _is_fabricated(pred, case.document_text)
        if fabricated:
            counters.fabricated += 1
            if not case.expect_fabrication:
                failures.append(f"{name}: fabricated KNOWN value without grounding")

        field_details[name] = detail

    passed = not failures
    counters.passed = passed
    return CaseScore(
        case_id=case.case_id,
        category=case.category,
        passed=passed,
        failures=failures,
        counters=counters,
        pred_status=pred_status,
        field_details=field_details,
    )


def _gold_dict(gold: GoldField) -> dict[str, Any]:
    return {
        "presence": gold.presence,
        "value": gold.value,
        "require_evidence": gold.require_evidence,
    }


def _values_equal(pred: Any, gold: Any, *, presence: str) -> bool:
    if presence != FieldPresence.KNOWN.value:
        return pred is None and gold is None
    if pred is None or gold is None:
        return pred is gold
    if isinstance(pred, str) and isinstance(gold, str):
        return _norm(pred) == _norm(gold)
    return bool(pred == gold)


def _norm(value: str) -> str:
    return _WS.sub(" ", value).strip().lower()


def _is_fabricated(field: ExtractedField, document_text: str) -> bool:
    if field.presence != FieldPresence.KNOWN:
        return False
    if field.value is None:
        return True
    text = _norm(document_text)
    value = _norm(str(field.value))
    if value and value not in text:
        return True
    if not field.evidence:
        return True
    for evidence in field.evidence:
        snippet = evidence.snippet
        if snippet and _norm(snippet) in text:
            return False
    return True


def _schema_valid(result: ExtractionResult) -> bool:
    try:
        # Re-validate via model_validate round-trip.
        ExtractionResult.model_validate(result.model_dump(mode="python"))
    except Exception:
        return False
    if result.status == ExtractionStatus.FAILED:
        return bool(result.errors or result.error_code)
    for extracted in result.fields:
        if extracted.presence == FieldPresence.KNOWN:
            if extracted.value is None or not extracted.evidence:
                return False
        elif extracted.value is not None:
            return False
    return True
