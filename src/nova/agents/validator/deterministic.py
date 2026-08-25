"""Deterministic rule evaluation for the Validator agent."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from nova.contracts.common import Evidence, EvidenceSourceType, FieldPresence, UncertaintyFlag
from nova.contracts.extraction import ExtractedField
from nova.contracts.validation import CustomerRuleSnapshot, ValidationCheck, ValidationOutcome

ENGINE_VERSION = "validator-det-1.0.0"
DEFAULT_CONFIDENCE_FLOOR = 0.5


def _evidence_ok(field: ExtractedField | None) -> bool:
    if field is None or not field.evidence:
        return False
    return any(e.source_type != EvidenceSourceType.NONE for e in field.evidence)


def _field_map(fields: list[ExtractedField]) -> dict[str, ExtractedField]:
    return {f.field_name: f for f in fields}


def _normalize_str(value: Any, *, casefold: bool = True) -> str:
    text = str(value).strip()
    return text.casefold() if casefold else text


def _parse_number(value: Any) -> Decimal | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int | float):
        return Decimal(str(value))
    if isinstance(value, str):
        try:
            return Decimal(value.strip().replace(",", ""))
        except InvalidOperation:
            return None
    return None


def _parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        except ValueError:
            return None
    return None


def _copy_evidence(field: ExtractedField | None) -> list[Evidence]:
    if field is None:
        return []
    return [e.model_copy(deep=True) for e in field.evidence]


def _has_verified_evidence(field: ExtractedField) -> bool:
    """KNOWN values require at least one non-NONE evidence source."""
    return any(e.source_type != EvidenceSourceType.NONE for e in field.evidence)


def _base_check(
    rule: CustomerRuleSnapshot,
    *,
    field_name: str | None,
    outcome: ValidationOutcome,
    reason: str,
    trace_id: UUID,
    run_id: UUID | None = None,
    expected: Any = None,
    actual: Any = None,
    confidence: float | None = None,
    evidence: list[Evidence] | None = None,
    details: dict[str, Any] | None = None,
    deterministic: bool = True,
) -> ValidationCheck:
    return ValidationCheck(
        trace_id=trace_id,
        run_id=run_id or rule.run_id,
        document_id=rule.document_id,
        document_version_id=rule.document_version_id,
        shipment_id=rule.shipment_id,
        customer_id=rule.customer_id,
        rule_id=rule.rule_id,
        rule_code=rule.rule_code,
        field_name=field_name,
        expected_value=expected,
        actual_value=actual,
        outcome=outcome,
        reason=reason,
        confidence=confidence,
        evidence=list(evidence or []),
        deterministic=deterministic,
        severity=rule.severity,
        blocking=rule.blocking,
        details={"validation_code": reason, **(details or {})},
    )


def evaluate_deterministic_rule(
    rule: CustomerRuleSnapshot,
    fields: list[ExtractedField],
    *,
    trace_id: UUID,
    run_id: UUID | None = None,
    confidence_floor: float = DEFAULT_CONFIDENCE_FLOOR,
) -> ValidationCheck:
    expr = rule.expression or {}
    op = str(expr.get("op") or expr.get("kind") or "").lower()
    fmap = _field_map(fields)
    field_name = expr.get("field") if isinstance(expr.get("field"), str) else None
    field = fmap.get(field_name) if field_name else None

    if not op:
        return _base_check(
            rule,
            field_name=field_name,
            outcome=ValidationOutcome.UNCERTAIN,
            reason="RULE_EXPRESSION_INVALID",
            trace_id=trace_id,
            run_id=run_id,
        )

    if op in {"required", "required_presence", "presence", "must_present"}:
        if field is None or field.presence != FieldPresence.KNOWN or field.value is None:
            code = "FIELD_MISSING"
            if field is not None and field.presence == FieldPresence.UNKNOWN:
                code = "FIELD_UNKNOWN"
            if field is not None and field.presence == FieldPresence.AMBIGUOUS:
                code = "FIELD_AMBIGUOUS"
            return _base_check(
                rule,
                field_name=field_name,
                outcome=ValidationOutcome.MISMATCH,
                reason=code,
                trace_id=trace_id,
                run_id=run_id,
                evidence=_copy_evidence(field),
            )
        return _base_check(
            rule,
            field_name=field_name,
            outcome=ValidationOutcome.MATCH,
            reason="MATCH",
            trace_id=trace_id,
            run_id=run_id,
            actual=field.value,
            confidence=field.confidence,
            evidence=_copy_evidence(field),
        )

    if op in {"cross_field", "cross_field_equals", "fields_equal"}:
        left_name = expr.get("left_field") or expr.get("field")
        right_name = expr.get("right_field") or expr.get("other_field")
        fields_list = expr.get("fields")
        if (
            (not isinstance(left_name, str) or not isinstance(right_name, str))
            and isinstance(fields_list, list)
            and len(fields_list) >= 2
        ):
            left_name, right_name = str(fields_list[0]), str(fields_list[1])
        if not isinstance(left_name, str) or not isinstance(right_name, str):
            return _base_check(
                rule,
                field_name=field_name,
                outcome=ValidationOutcome.UNCERTAIN,
                reason="RULE_EXPRESSION_INVALID",
                trace_id=trace_id,
                run_id=run_id,
            )
        left_field = fmap.get(left_name)
        right_field = fmap.get(right_name)
        if (
            left_field is None
            or right_field is None
            or left_field.presence != FieldPresence.KNOWN
            or right_field.presence != FieldPresence.KNOWN
        ):
            return _base_check(
                rule,
                field_name=f"{left_name},{right_name}",
                outcome=ValidationOutcome.UNCERTAIN,
                reason="FIELD_UNKNOWN",
                trace_id=trace_id,
                run_id=run_id,
            )
        if not _evidence_ok(left_field) or not _evidence_ok(right_field):
            return _base_check(
                rule,
                field_name=f"{left_name},{right_name}",
                outcome=ValidationOutcome.UNCERTAIN,
                reason="MISSING_EVIDENCE",
                trace_id=trace_id,
                run_id=run_id,
            )
        ok = _normalize_str(left_field.value) == _normalize_str(right_field.value)
        return _base_check(
            rule,
            field_name=f"{left_name},{right_name}",
            outcome=ValidationOutcome.MATCH if ok else ValidationOutcome.MISMATCH,
            reason="MATCH" if ok else "CROSS_FIELD_MISMATCH",
            trace_id=trace_id,
            run_id=run_id,
            expected=right_field.value,
            actual=left_field.value,
            confidence=min(
                filter(None, [left_field.confidence, right_field.confidence]), default=None
            ),
            evidence=_copy_evidence(left_field) + _copy_evidence(right_field),
        )

    if op in {"judgment", "custom"}:
        return _base_check(
            rule,
            field_name=field_name,
            outcome=ValidationOutcome.UNCERTAIN,
            reason="REQUIRES_JUDGMENT",
            trace_id=trace_id,
            run_id=run_id,
            confidence=None,
            details={"op": op},
        )

    if field is None or field.presence != FieldPresence.KNOWN or field.value is None:
        if field is not None and field.presence == FieldPresence.AMBIGUOUS:
            reason = "FIELD_AMBIGUOUS"
        elif field is None or field.presence == FieldPresence.MISSING:
            reason = "FIELD_MISSING"
        else:
            reason = "FIELD_UNKNOWN"
        return _base_check(
            rule,
            field_name=field_name,
            outcome=ValidationOutcome.UNCERTAIN,
            reason=reason,
            trace_id=trace_id,
            run_id=run_id,
            evidence=_copy_evidence(field),
        )

    if not _evidence_ok(field):
        return _base_check(
            rule,
            field_name=field_name,
            outcome=ValidationOutcome.UNCERTAIN,
            reason="MISSING_EVIDENCE",
            trace_id=trace_id,
            run_id=run_id,
            actual=field.value,
            confidence=field.confidence,
        )

    if field.uncertainty == UncertaintyFlag.CONFLICTING_EVIDENCE:
        return _base_check(
            rule,
            field_name=field_name,
            outcome=ValidationOutcome.UNCERTAIN,
            reason="CONFLICTING_EVIDENCE",
            trace_id=trace_id,
            run_id=run_id,
            actual=field.value,
            confidence=field.confidence,
            evidence=_copy_evidence(field),
        )

    min_conf = expr.get("min_confidence", confidence_floor if op != "required" else None)
    if min_conf is not None:
        try:
            threshold = float(min_conf)
        except (TypeError, ValueError):
            threshold = None
        if threshold is not None and (field.confidence is None or field.confidence < threshold):
            return _base_check(
                rule,
                field_name=field_name,
                outcome=ValidationOutcome.UNCERTAIN,
                reason="LOW_CONFIDENCE",
                trace_id=trace_id,
                run_id=run_id,
                expected=threshold,
                actual=field.confidence,
                confidence=field.confidence,
                evidence=_copy_evidence(field),
            )

    if op in {"equals", "exact", "string_equals", "equality", "eq"}:
        expected = expr.get("expected")
        left = _normalize_str(field.value)
        right = _normalize_str(expected)
        if left == right:
            return _base_check(
                rule,
                field_name=field_name,
                outcome=ValidationOutcome.MATCH,
                reason="MATCH",
                trace_id=trace_id,
                run_id=run_id,
                expected=expected,
                actual=field.value,
                confidence=field.confidence,
                evidence=_copy_evidence(field),
            )
        return _base_check(
            rule,
            field_name=field_name,
            outcome=ValidationOutcome.MISMATCH,
            reason="VALUE_MISMATCH",
            trace_id=trace_id,
            run_id=run_id,
            expected=expected,
            actual=field.value,
            confidence=field.confidence,
            evidence=_copy_evidence(field),
        )

    if op in {"format", "regex", "pattern"}:
        pattern = expr.get("pattern")
        if not isinstance(pattern, str):
            return _base_check(
                rule,
                field_name=field_name,
                outcome=ValidationOutcome.UNCERTAIN,
                reason="RULE_EXPRESSION_INVALID",
                trace_id=trace_id,
                run_id=run_id,
            )
        try:
            ok = re.fullmatch(pattern, str(field.value)) is not None
        except re.error:
            return _base_check(
                rule,
                field_name=field_name,
                outcome=ValidationOutcome.UNCERTAIN,
                reason="RULE_EXPRESSION_INVALID",
                trace_id=trace_id,
                run_id=run_id,
            )
        return _base_check(
            rule,
            field_name=field_name,
            outcome=ValidationOutcome.MATCH if ok else ValidationOutcome.MISMATCH,
            reason="MATCH" if ok else "FORMAT_MISMATCH",
            trace_id=trace_id,
            run_id=run_id,
            expected=pattern,
            actual=field.value,
            confidence=field.confidence,
            evidence=_copy_evidence(field),
        )

    if op in {"numeric", "numeric_tolerance", "number", "tolerance"}:
        expected = _parse_number(expr.get("expected"))
        actual = _parse_number(field.value)
        if expected is None or actual is None:
            return _base_check(
                rule,
                field_name=field_name,
                outcome=ValidationOutcome.UNCERTAIN,
                reason="TYPE_INCOMPATIBLE",
                trace_id=trace_id,
                run_id=run_id,
                expected=expr.get("expected"),
                actual=field.value,
                confidence=field.confidence,
                evidence=_copy_evidence(field),
            )
        if "tolerance_abs" in expr:
            tol = _parse_number(expr["tolerance_abs"]) or Decimal("0")
            ok = abs(actual - expected) <= abs(tol)
        else:
            pct = _parse_number(expr.get("tolerance_pct", 0)) or Decimal("0")
            if expected == 0:
                ok = actual == 0
            else:
                ok = abs(actual - expected) <= abs(expected) * (pct / Decimal("100"))
        return _base_check(
            rule,
            field_name=field_name,
            outcome=ValidationOutcome.MATCH if ok else ValidationOutcome.MISMATCH,
            reason="MATCH" if ok else "NUMERIC_OUT_OF_TOLERANCE",
            trace_id=trace_id,
            run_id=run_id,
            expected=expr.get("expected"),
            actual=field.value,
            confidence=field.confidence,
            evidence=_copy_evidence(field),
        )

    if op in {"date", "date_equals", "date_match"}:
        expected_date = _parse_date(expr.get("expected"))
        actual_date = _parse_date(field.value)
        if expected_date is None or actual_date is None:
            return _base_check(
                rule,
                field_name=field_name,
                outcome=ValidationOutcome.UNCERTAIN,
                reason="TYPE_INCOMPATIBLE",
                trace_id=trace_id,
                run_id=run_id,
                expected=expr.get("expected"),
                actual=field.value,
                confidence=field.confidence,
                evidence=_copy_evidence(field),
            )
        ok = expected_date == actual_date
        return _base_check(
            rule,
            field_name=field_name,
            outcome=ValidationOutcome.MATCH if ok else ValidationOutcome.MISMATCH,
            reason="MATCH" if ok else "DATE_MISMATCH",
            trace_id=trace_id,
            run_id=run_id,
            expected=expr.get("expected"),
            actual=field.value,
            confidence=field.confidence,
            evidence=_copy_evidence(field),
        )

    return _base_check(
        rule,
        field_name=field_name,
        outcome=ValidationOutcome.UNCERTAIN,
        reason="UNKNOWN_RULE_OP",
        trace_id=trace_id,
        run_id=run_id,
        details={"op": op},
    )
