"""Deterministic document confidence / agreement classification.

Analytical layer over existing extraction confidence + validation outcomes.
Orthogonal to Router DecisionKind (AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class AgreementCategory(StrEnum):
    STRONG_AGREEMENT = "STRONG_AGREEMENT"
    PARTIAL_AGREEMENT = "PARTIAL_AGREEMENT"
    WEAK_AGREEMENT = "WEAK_AGREEMENT"


# Align with confidence bands / routing policy defaults (see confidence-and-evidence.md).
HIGH_CONFIDENCE_THRESHOLD = 0.85
LOW_CONFIDENCE_THRESHOLD = 0.60

# How much a required field contributes to document agreement, given its
# validation outcome. Extraction confidence answers "did we read it right";
# these factors answer "does the value agree with the customer's expectation".
MATCH_FACTOR = 1.0
UNCERTAIN_FACTOR = 0.5
MISMATCH_FACTOR = 0.0
UNVALIDATED_FACTOR = 0.5
AMBIGUOUS_FACTOR = 0.25


@dataclass(frozen=True)
class FieldConfidenceInput:
    field_name: str
    confidence: float | None
    presence: str | None = None
    is_missing: bool = False


@dataclass(frozen=True)
class ValidationCheckInput:
    field_name: str | None
    outcome: str


@dataclass(frozen=True)
class DocumentAgreement:
    """Document-level reliability.

    ``document_confidence`` is the *agreement* score: how strongly the whole
    document agrees with the customer's configured expectations. It combines
    extraction confidence with validation outcomes, so a confidently-read but
    mismatching value scores low.

    ``extraction_confidence`` is the separate "did the extractor read the text
    correctly" average. High extraction confidence with a MISMATCH is normal
    and must not produce high agreement.
    """

    category: AgreementCategory
    document_confidence: float | None
    reasons: tuple[str, ...]
    extraction_confidence: float | None = None

    @property
    def document_confidence_percent(self) -> int | None:
        return _percent(self.document_confidence)

    @property
    def extraction_confidence_percent(self) -> int | None:
        return _percent(self.extraction_confidence)


def _percent(value: float | None) -> int | None:
    if value is None:
        return None
    return int(round(value * 100))


def average_required_confidence(
    required_fields: Sequence[str],
    fields: Sequence[FieldConfidenceInput],
) -> float | None:
    """Average confidence of required fields that have real scores.

    Never invents scores. Missing/unknown required fields are skipped for the
    average; callers use ``missing_required_confidence`` for completeness.
    Returns None only when no required field has a usable confidence value.
    """
    by_name = {item.field_name: item for item in fields}
    scores: list[float] = []
    for name in required_fields:
        item = by_name.get(name)
        if item is None or item.is_missing:
            continue
        presence = (item.presence or "").upper()
        if presence in {"MISSING", "UNKNOWN", "AMBIGUOUS"}:
            continue
        if item.confidence is None:
            continue
        scores.append(float(item.confidence))
    if not scores:
        return None
    return round(sum(scores) / len(scores), 6)


def missing_required_confidence(
    required_fields: Sequence[str],
    fields: Sequence[FieldConfidenceInput],
) -> bool:
    """True when any required field lacks a usable extraction confidence."""
    by_name = {item.field_name: item for item in fields}
    for name in required_fields:
        item = by_name.get(name)
        if item is None or item.is_missing:
            return True
        presence = (item.presence or "").upper()
        if presence in {"MISSING", "UNKNOWN", "AMBIGUOUS"}:
            return True
        if item.confidence is None:
            return True
    return False


def _worst_outcome_by_field(
    checks: Sequence[ValidationCheckInput],
) -> dict[str, str]:
    """Worst validation outcome per field (a field is only as good as its worst check)."""
    worst: dict[str, str] = {}
    for check in checks:
        name = check.field_name
        if not name:
            continue
        outcome = str(check.outcome or "").upper()
        prior = worst.get(name)
        if prior is None or _outcome_rank(outcome) > _outcome_rank(prior):
            worst[name] = outcome
    return worst


def agreement_score(
    required_fields: Sequence[str],
    fields: Sequence[FieldConfidenceInput],
    checks: Sequence[ValidationCheckInput],
) -> float | None:
    """Document agreement over required fields, from extraction + validation evidence.

    Each required field contributes ``extraction_confidence * outcome_factor``.
    Fields with no evidence (MISSING/UNKNOWN) or a MISMATCH contribute zero, so
    absent and disagreeing evidence materially reduce the document score. The
    denominator is always the full required-field count, so a document cannot
    score highly by validating only a handful of fields.
    """
    if not required_fields:
        return None

    by_name = {item.field_name: item for item in fields}
    outcomes = _worst_outcome_by_field(checks)

    total = 0.0
    for name in required_fields:
        item = by_name.get(name)
        if item is None or item.is_missing:
            continue

        presence = (item.presence or "").upper()
        if presence in {"MISSING", "UNKNOWN"}:
            continue
        if item.confidence is None:
            continue

        base = float(item.confidence)
        if presence == "AMBIGUOUS":
            total += base * AMBIGUOUS_FACTOR
            continue

        outcome = outcomes.get(name)
        if outcome is None:
            total += base * UNVALIDATED_FACTOR
        elif outcome == "MATCH":
            total += base * MATCH_FACTOR
        elif outcome == "UNCERTAIN":
            total += base * UNCERTAIN_FACTOR
        elif outcome == "MISMATCH":
            total += base * MISMATCH_FACTOR
        else:
            total += base * UNVALIDATED_FACTOR

    return round(total / len(required_fields), 6)


def classify_document_agreement(
    *,
    required_fields: Sequence[str],
    fields: Sequence[FieldConfidenceInput],
    validation_status: str | None,
    checks: Sequence[ValidationCheckInput],
    high_confidence_threshold: float = HIGH_CONFIDENCE_THRESHOLD,
    low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD,
) -> DocumentAgreement:
    """Classify agreement from persisted extraction + validation evidence only."""
    reasons: list[str] = []
    extraction = average_required_confidence(required_fields, fields)
    score = agreement_score(required_fields, fields, checks)
    incomplete_extraction = missing_required_confidence(required_fields, fields)

    def result(category: AgreementCategory, reason: str) -> DocumentAgreement:
        reasons.append(reason)
        return DocumentAgreement(
            category=category,
            document_confidence=score,
            reasons=tuple(reasons),
            extraction_confidence=extraction,
        )

    status = (validation_status or "").strip().lower()
    if not status or status not in {"completed", "complete"}:
        return result(AgreementCategory.WEAK_AGREEMENT, "validation_missing_or_incomplete")

    outcomes = [str(check.outcome or "").upper() for check in checks]
    mismatch_count = sum(1 for outcome in outcomes if outcome == "MISMATCH")
    uncertain_count = sum(1 for outcome in outcomes if outcome == "UNCERTAIN")
    match_count = sum(1 for outcome in outcomes if outcome == "MATCH")

    if mismatch_count:
        return result(AgreementCategory.WEAK_AGREEMENT, "validation_mismatch")

    if incomplete_extraction or extraction is None:
        return result(
            AgreementCategory.WEAK_AGREEMENT,
            "missing_required_extraction_confidence",
        )

    if extraction < low_confidence_threshold:
        return result(AgreementCategory.WEAK_AGREEMENT, "low_extraction_confidence")

    required_set = set(required_fields)
    required_outcomes = {
        name: outcome
        for name, outcome in _worst_outcome_by_field(checks).items()
        if name in required_set
    }

    missing_required_checks = [name for name in required_fields if name not in required_outcomes]
    if missing_required_checks:
        return result(AgreementCategory.WEAK_AGREEMENT, "incomplete_required_validation")

    required_uncertain = [
        name for name, outcome in required_outcomes.items() if outcome == "UNCERTAIN"
    ]
    all_required_match = all(outcome == "MATCH" for outcome in required_outcomes.values())
    any_uncertain = uncertain_count > 0

    if (
        all_required_match
        and not any_uncertain
        and not required_uncertain
        and extraction >= high_confidence_threshold
        and score is not None
        and score >= high_confidence_threshold
    ):
        return result(
            AgreementCategory.STRONG_AGREEMENT,
            "all_required_match_high_confidence",
        )

    if match_count > 0 and (
        any_uncertain
        or required_uncertain
        or extraction < high_confidence_threshold
        or not all_required_match
    ):
        return result(
            AgreementCategory.PARTIAL_AGREEMENT,
            "partial_alignment_requires_attention",
        )

    return result(AgreementCategory.WEAK_AGREEMENT, "insufficient_evidence_for_strong")


def _outcome_rank(outcome: str) -> int:
    if outcome == "MISMATCH":
        return 3
    if outcome == "UNCERTAIN":
        return 2
    if outcome == "MATCH":
        return 1
    return 0


def agreement_wire(result: DocumentAgreement) -> dict[str, object]:
    """Stable API projection for agreement (orthogonal to decision).

    ``document_confidence`` is the agreement score; ``extraction_confidence`` is
    reported alongside it so consumers can tell "read correctly" apart from
    "agrees with expectations".
    """
    return {
        "agreement": result.category.value,
        "document_confidence": result.document_confidence,
        "document_confidence_percent": result.document_confidence_percent,
        "extraction_confidence": result.extraction_confidence,
        "extraction_confidence_percent": result.extraction_confidence_percent,
        "agreement_reasons": list(result.reasons),
    }
