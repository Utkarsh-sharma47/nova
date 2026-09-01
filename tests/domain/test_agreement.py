"""Unit tests for deterministic document agreement classification."""

from __future__ import annotations

from nova.domain.agreement import (
    AgreementCategory,
    FieldConfidenceInput,
    ValidationCheckInput,
    classify_document_agreement,
)

_REQUIRED = (
    "consignee_name",
    "hs_code",
    "port_of_loading",
    "port_of_discharge",
    "incoterms",
    "description_of_goods",
    "gross_weight",
    "invoice_number",
)


def _fields(confidence: float = 0.95) -> list[FieldConfidenceInput]:
    return [
        FieldConfidenceInput(field_name=name, confidence=confidence, presence="KNOWN")
        for name in _REQUIRED
    ]


def _checks(*pairs: tuple[str, str]) -> list[ValidationCheckInput]:
    return [ValidationCheckInput(field_name=name, outcome=outcome) for name, outcome in pairs]


def _all_match() -> list[ValidationCheckInput]:
    return _checks(*[(name, "MATCH") for name in _REQUIRED])


def test_strong_agreement_all_match_high_confidence() -> None:
    result = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=_fields(0.94),
        validation_status="completed",
        checks=_all_match(),
    )
    assert result.category == AgreementCategory.STRONG_AGREEMENT
    assert result.document_confidence is not None
    assert result.document_confidence_percent == 94


def test_partial_agreement_uncertain_field() -> None:
    checks = _all_match()
    checks[0] = ValidationCheckInput(field_name="consignee_name", outcome="UNCERTAIN")
    result = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=_fields(0.92),
        validation_status="completed",
        checks=checks,
    )
    assert result.category == AgreementCategory.PARTIAL_AGREEMENT


def test_weak_agreement_mismatch() -> None:
    checks = _all_match()
    checks[0] = ValidationCheckInput(field_name="consignee_name", outcome="MISMATCH")
    result = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=_fields(0.99),
        validation_status="completed",
        checks=checks,
    )
    assert result.category == AgreementCategory.WEAK_AGREEMENT
    assert AgreementCategory.STRONG_AGREEMENT != result.category


def test_weak_agreement_missing_validation() -> None:
    result = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=_fields(0.99),
        validation_status=None,
        checks=[],
    )
    assert result.category == AgreementCategory.WEAK_AGREEMENT


def test_missing_required_extraction_not_strong() -> None:
    fields = _fields(0.95)[1:]  # drop consignee_name
    result = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=fields,
        validation_status="completed",
        checks=_all_match(),
    )
    assert result.category != AgreementCategory.STRONG_AGREEMENT
    assert result.category == AgreementCategory.WEAK_AGREEMENT
    # Extraction confidence reflects available fields only; never fabricated.
    assert result.extraction_confidence == 0.95
    # ...but a required field with no evidence must reduce document agreement.
    assert result.document_confidence is not None
    assert result.document_confidence < 0.95


def test_document_confidence_differs_for_different_field_scores() -> None:
    high = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=_fields_custom([0.98, 0.97, 0.95]),
        validation_status="completed",
        checks=_all_match(),
    )
    low = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=_fields_custom([0.65, 0.72, 0.61]),
        validation_status="completed",
        checks=_all_match(),
    )
    assert high.document_confidence is not None
    assert low.document_confidence is not None
    assert high.document_confidence > low.document_confidence
    assert high.document_confidence_percent != low.document_confidence_percent


def _fields_custom(cycle: list[float]) -> list[FieldConfidenceInput]:
    out: list[FieldConfidenceInput] = []
    for index, name in enumerate(_REQUIRED):
        out.append(
            FieldConfidenceInput(
                field_name=name,
                confidence=cycle[index % len(cycle)],
                presence="KNOWN",
            )
        )
    return out


def test_low_extraction_confidence_not_strong() -> None:
    result = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=_fields(0.4),
        validation_status="completed",
        checks=_all_match(),
    )
    assert result.category != AgreementCategory.STRONG_AGREEMENT
    assert result.category == AgreementCategory.WEAK_AGREEMENT


def test_medium_confidence_is_partial_when_all_match() -> None:
    result = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=_fields(0.72),
        validation_status="completed",
        checks=_all_match(),
    )
    assert result.category == AgreementCategory.PARTIAL_AGREEMENT


def test_confident_extraction_with_mismatches_is_not_high_agreement() -> None:
    """The core bug: confident reads of wrong values must not score ~93%."""
    all_match = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=_fields(0.96),
        validation_status="completed",
        checks=_all_match(),
    )
    mostly_mismatch = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=_fields(0.96),
        validation_status="completed",
        checks=_checks(
            (_REQUIRED[0], "MATCH"),
            (_REQUIRED[1], "MATCH"),
            *[(name, "MISMATCH") for name in _REQUIRED[2:]],
        ),
    )

    # Extraction read the text equally well in both documents.
    assert all_match.extraction_confidence == mostly_mismatch.extraction_confidence == 0.96

    # Agreement must diverge sharply.
    assert all_match.category == AgreementCategory.STRONG_AGREEMENT
    assert mostly_mismatch.category == AgreementCategory.WEAK_AGREEMENT
    assert all_match.document_confidence is not None
    assert mostly_mismatch.document_confidence is not None
    assert mostly_mismatch.document_confidence < 0.40
    assert all_match.document_confidence > mostly_mismatch.document_confidence + 0.50


def test_each_additional_mismatch_reduces_agreement() -> None:
    def score_with(mismatches: int) -> float:
        checks = _checks(
            *[
                (name, "MISMATCH" if index < mismatches else "MATCH")
                for index, name in enumerate(_REQUIRED)
            ]
        )
        result = classify_document_agreement(
            required_fields=_REQUIRED,
            fields=_fields(0.95),
            validation_status="completed",
            checks=checks,
        )
        assert result.document_confidence is not None
        return result.document_confidence

    scores = [score_with(n) for n in range(len(_REQUIRED) + 1)]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] > scores[-1]
    assert scores[-1] == 0.0


def test_uncertain_is_not_treated_as_match() -> None:
    match = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=_fields(0.95),
        validation_status="completed",
        checks=_all_match(),
    )
    uncertain = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=_fields(0.95),
        validation_status="completed",
        checks=_checks(*[(name, "UNCERTAIN") for name in _REQUIRED]),
    )
    assert uncertain.document_confidence is not None
    assert match.document_confidence is not None
    assert uncertain.document_confidence < match.document_confidence
    assert uncertain.category != AgreementCategory.STRONG_AGREEMENT


def test_ambiguous_field_reduces_agreement() -> None:
    fields = _fields(0.95)
    fields[0] = FieldConfidenceInput(
        field_name=_REQUIRED[0],
        confidence=0.95,
        presence="AMBIGUOUS",
    )
    ambiguous = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=fields,
        validation_status="completed",
        checks=_all_match(),
    )
    clean = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=_fields(0.95),
        validation_status="completed",
        checks=_all_match(),
    )
    assert ambiguous.document_confidence is not None
    assert clean.document_confidence is not None
    assert ambiguous.document_confidence < clean.document_confidence
    assert ambiguous.category != AgreementCategory.STRONG_AGREEMENT


def test_failed_validation_is_weak() -> None:
    result = classify_document_agreement(
        required_fields=_REQUIRED,
        fields=_fields(0.95),
        validation_status="failed",
        checks=_all_match(),
    )
    assert result.category == AgreementCategory.WEAK_AGREEMENT
