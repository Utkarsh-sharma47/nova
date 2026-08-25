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
    category: AgreementCategory
    document_confidence: float | None
    reasons: tuple[str, ...]

    @property
    def document_confidence_percent(self) -> int | None:
        if self.document_confidence is None:
            return None
        return int(round(self.document_confidence * 100))


def average_required_confidence(
    required_fields: Sequence[str],
    fields: Sequence[FieldConfidenceInput],
) -> float | None:
    """Average confidence of required extracted fields.

    Returns None when any required field is missing or lacks a numeric confidence
    (never invents scores).
    """
    by_name = {item.field_name: item for item in fields}
    scores: list[float] = []
    for name in required_fields:
        item = by_name.get(name)
        if item is None or item.is_missing:
            return None
        presence = (item.presence or "").upper()
        if presence in {"MISSING", "UNKNOWN", "AMBIGUOUS"}:
            return None
        if item.confidence is None:
            return None
        scores.append(float(item.confidence))
    if not scores:
        return None
    return round(sum(scores) / len(scores), 6)


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
    document_confidence = average_required_confidence(required_fields, fields)

    status = (validation_status or "").strip().lower()
    if not status or status not in {"completed", "complete"}:
        reasons.append("validation_missing_or_incomplete")
        return DocumentAgreement(
            category=AgreementCategory.WEAK_AGREEMENT,
            document_confidence=document_confidence,
            reasons=tuple(reasons),
        )

    outcomes = [str(check.outcome or "").upper() for check in checks]
    mismatch_count = sum(1 for outcome in outcomes if outcome == "MISMATCH")
    uncertain_count = sum(1 for outcome in outcomes if outcome == "UNCERTAIN")
    match_count = sum(1 for outcome in outcomes if outcome == "MATCH")

    if mismatch_count:
        reasons.append("validation_mismatch")
        return DocumentAgreement(
            category=AgreementCategory.WEAK_AGREEMENT,
            document_confidence=document_confidence,
            reasons=tuple(reasons),
        )

    if document_confidence is None:
        reasons.append("missing_required_extraction_confidence")
        return DocumentAgreement(
            category=AgreementCategory.WEAK_AGREEMENT,
            document_confidence=None,
            reasons=tuple(reasons),
        )

    if document_confidence < low_confidence_threshold:
        reasons.append("low_extraction_confidence")
        return DocumentAgreement(
            category=AgreementCategory.WEAK_AGREEMENT,
            document_confidence=document_confidence,
            reasons=tuple(reasons),
        )

    required_set = set(required_fields)
    required_outcomes: dict[str, str] = {}
    for check in checks:
        name = check.field_name
        if not name or name not in required_set:
            continue
        outcome = str(check.outcome or "").upper()
        # Prefer worst outcome if multiple checks touch the same field.
        prior = required_outcomes.get(name)
        if prior is None or _outcome_rank(outcome) > _outcome_rank(prior):
            required_outcomes[name] = outcome

    missing_required_checks = [name for name in required_fields if name not in required_outcomes]
    if missing_required_checks:
        reasons.append("incomplete_required_validation")
        return DocumentAgreement(
            category=AgreementCategory.WEAK_AGREEMENT,
            document_confidence=document_confidence,
            reasons=tuple(reasons),
        )

    required_uncertain = [
        name for name, outcome in required_outcomes.items() if outcome == "UNCERTAIN"
    ]
    all_required_match = all(outcome == "MATCH" for outcome in required_outcomes.values())
    any_uncertain = uncertain_count > 0

    if (
        all_required_match
        and not any_uncertain
        and not required_uncertain
        and document_confidence >= high_confidence_threshold
    ):
        reasons.append("all_required_match_high_confidence")
        return DocumentAgreement(
            category=AgreementCategory.STRONG_AGREEMENT,
            document_confidence=document_confidence,
            reasons=tuple(reasons),
        )

    if match_count > 0 and (
        any_uncertain
        or required_uncertain
        or document_confidence < high_confidence_threshold
        or not all_required_match
    ):
        reasons.append("partial_alignment_requires_attention")
        return DocumentAgreement(
            category=AgreementCategory.PARTIAL_AGREEMENT,
            document_confidence=document_confidence,
            reasons=tuple(reasons),
        )

    reasons.append("insufficient_evidence_for_strong")
    return DocumentAgreement(
        category=AgreementCategory.WEAK_AGREEMENT,
        document_confidence=document_confidence,
        reasons=tuple(reasons),
    )


def _outcome_rank(outcome: str) -> int:
    if outcome == "MISMATCH":
        return 3
    if outcome == "UNCERTAIN":
        return 2
    if outcome == "MATCH":
        return 1
    return 0


def agreement_wire(result: DocumentAgreement) -> dict[str, object]:
    """Stable API projection for agreement (orthogonal to decision)."""
    return {
        "agreement": result.category.value,
        "document_confidence": result.document_confidence,
        "document_confidence_percent": result.document_confidence_percent,
        "agreement_reasons": list(result.reasons),
    }
