"""Deterministic safety constraints for the Router.

These run before any LLM suggestion is accepted and again as a final gate
before AUTO_APPROVE is emitted. Constraints never perform extraction or
re-validation — they only consume ExtractionResult + ValidationResult.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from nova.contracts.common import FieldPresence, UncertaintyFlag
from nova.contracts.extraction import ExtractionResult, ExtractionStatus
from nova.contracts.routing import DecisionKind, RoutingPolicySnapshot
from nova.contracts.validation import ValidationOutcome, ValidationResult, ValidationStatus
from nova.router.codes import (
    SC_AMBIGUOUS_FIELD,
    SC_BLOCKING_MISMATCH,
    SC_BLOCKING_UNCERTAIN,
    SC_CONFLICTING_EVIDENCE,
    SC_CONTRADICTORY_INPUTS,
    SC_EMPTY_CHECKS,
    SC_EXTRACTION_FAILED,
    SC_EXTRACTION_PARTIAL,
    SC_FABRICATED_EVIDENCE,
    SC_LLM_FAILURE,
    SC_LOW_CONFIDENCE,
    SC_MALFORMED_OUTPUT,
    SC_MISSING_EVIDENCE,
    SC_MISSING_FIELD,
    SC_POLICY_DENY_UNKNOWN,
    SC_SYSTEM_FAILSAFE,
    SC_TIMEOUT,
    SC_UNKNOWN_FIELD,
    SC_VALIDATION_FAILED,
)


@dataclass(frozen=True)
class SafetyHit:
    code: str
    reason: str
    preferred_decision: DecisionKind
    triggering_check_ids: tuple[UUID, ...] = ()


@dataclass
class SafetyAssessment:
    hits: list[SafetyHit] = field(default_factory=list)

    @property
    def blocks_auto_approve(self) -> bool:
        return bool(self.hits)

    @property
    def codes(self) -> list[str]:
        return [h.code for h in self.hits]

    @property
    def reasons(self) -> list[str]:
        return [h.reason for h in self.hits]

    @property
    def triggering_check_ids(self) -> list[UUID]:
        seen: set[UUID] = set()
        out: list[UUID] = []
        for hit in self.hits:
            for cid in hit.triggering_check_ids:
                if cid not in seen:
                    seen.add(cid)
                    out.append(cid)
        return out

    def preferred_decision(self) -> DecisionKind:
        """Prefer AMENDMENT_REQUEST only for pure blocking mismatches."""
        review_codes = {
            SC_BLOCKING_UNCERTAIN,
            SC_VALIDATION_FAILED,
            SC_EXTRACTION_FAILED,
            SC_EXTRACTION_PARTIAL,
            SC_LOW_CONFIDENCE,
            SC_MISSING_FIELD,
            SC_UNKNOWN_FIELD,
            SC_AMBIGUOUS_FIELD,
            SC_MISSING_EVIDENCE,
            SC_EMPTY_CHECKS,
            SC_CONTRADICTORY_INPUTS,
            SC_POLICY_DENY_UNKNOWN,
            SC_CONFLICTING_EVIDENCE,
            SC_FABRICATED_EVIDENCE,
            SC_LLM_FAILURE,
            SC_MALFORMED_OUTPUT,
            SC_SYSTEM_FAILSAFE,
            SC_TIMEOUT,
        }
        has_mismatch = any(h.code == SC_BLOCKING_MISMATCH for h in self.hits)
        has_review = any(h.code in review_codes for h in self.hits)
        if has_mismatch and not has_review:
            return DecisionKind.AMENDMENT_REQUEST
        return DecisionKind.HUMAN_REVIEW


def evaluate_safety_constraints(
    *,
    extraction: ExtractionResult,
    validation: ValidationResult,
    policy: RoutingPolicySnapshot,
    blocking_uncertainty_present: bool = False,
) -> SafetyAssessment:
    assessment = SafetyAssessment()

    if validation.status == ValidationStatus.FAILED or validation.errors or validation.error_code:
        assessment.hits.append(
            SafetyHit(
                code=SC_VALIDATION_FAILED,
                reason="Validation stage failed; AUTO_APPROVE forbidden",
                preferred_decision=DecisionKind.HUMAN_REVIEW,
            )
        )

    if extraction.status == ExtractionStatus.FAILED:
        assessment.hits.append(
            SafetyHit(
                code=SC_EXTRACTION_FAILED,
                reason="Extraction stage failed; AUTO_APPROVE forbidden",
                preferred_decision=DecisionKind.HUMAN_REVIEW,
            )
        )
    elif extraction.status == ExtractionStatus.PARTIAL:
        assessment.hits.append(
            SafetyHit(
                code=SC_EXTRACTION_PARTIAL,
                reason="Partial extraction; AUTO_APPROVE forbidden",
                preferred_decision=DecisionKind.HUMAN_REVIEW,
            )
        )

    if validation.status == ValidationStatus.COMPLETED and not validation.checks:
        assessment.hits.append(
            SafetyHit(
                code=SC_EMPTY_CHECKS,
                reason="Completed validation produced no checks; fail closed",
                preferred_decision=DecisionKind.HUMAN_REVIEW,
            )
        )

    # Contradictory: validation claims MATCH counts but checks disagree.
    derived_mismatch = sum(
        1 for c in validation.checks if c.outcome == ValidationOutcome.MISMATCH
    )
    derived_uncertain = sum(
        1 for c in validation.checks if c.outcome == ValidationOutcome.UNCERTAIN
    )
    if (
        validation.mismatch_count != derived_mismatch
        or validation.uncertain_count != derived_uncertain
    ):
        assessment.hits.append(
            SafetyHit(
                code=SC_CONTRADICTORY_INPUTS,
                reason="Validation summary counts contradict check outcomes",
                preferred_decision=DecisionKind.HUMAN_REVIEW,
            )
        )

    # Contradictory: same rule_id emits conflicting outcomes in one result.
    outcomes_by_rule: dict[UUID, set[ValidationOutcome]] = {}
    for check in validation.checks:
        outcomes_by_rule.setdefault(check.rule_id, set()).add(check.outcome)
    for rule_id, outcomes in outcomes_by_rule.items():
        if len(outcomes) > 1:
            assessment.hits.append(
                SafetyHit(
                    code=SC_CONTRADICTORY_INPUTS,
                    reason=f"Contradictory validation outcomes for rule {rule_id}",
                    preferred_decision=DecisionKind.HUMAN_REVIEW,
                    triggering_check_ids=(rule_id,),
                )
            )

    for check in validation.checks:
        if not check.blocking:
            continue
        if check.outcome == ValidationOutcome.MISMATCH:
            assessment.hits.append(
                SafetyHit(
                    code=SC_BLOCKING_MISMATCH,
                    reason=f"Blocking mismatch on rule {check.rule_code}",
                    preferred_decision=DecisionKind.AMENDMENT_REQUEST,
                    triggering_check_ids=(check.rule_id,),
                )
            )
        elif check.outcome == ValidationOutcome.UNCERTAIN:
            assessment.hits.append(
                SafetyHit(
                    code=SC_BLOCKING_UNCERTAIN,
                    reason=f"Blocking uncertainty on rule {check.rule_code}",
                    preferred_decision=DecisionKind.HUMAN_REVIEW,
                    triggering_check_ids=(check.rule_id,),
                )
            )

    if blocking_uncertainty_present and not any(
        h.code == SC_BLOCKING_UNCERTAIN for h in assessment.hits
    ):
        assessment.hits.append(
            SafetyHit(
                code=SC_BLOCKING_UNCERTAIN,
                reason="Caller flagged blocking uncertainty present",
                preferred_decision=DecisionKind.HUMAN_REVIEW,
            )
        )

    fields_by_name = {f.field_name: f for f in extraction.fields}
    critical = list(policy.critical_fields) or list(fields_by_name.keys())

    for name in critical:
        field = fields_by_name.get(name)
        if field is None:
            if not policy.allow_auto_approve_on_unknown:
                assessment.hits.append(
                    SafetyHit(
                        code=SC_MISSING_FIELD,
                        reason=f"Critical field '{name}' absent from extraction",
                        preferred_decision=DecisionKind.HUMAN_REVIEW,
                    )
                )
            continue

        if field.presence == FieldPresence.MISSING:
            assessment.hits.append(
                SafetyHit(
                    code=SC_MISSING_FIELD,
                    reason=f"Critical field '{name}' is MISSING",
                    preferred_decision=DecisionKind.HUMAN_REVIEW,
                )
            )
        elif field.presence == FieldPresence.UNKNOWN:
            code = (
                SC_POLICY_DENY_UNKNOWN
                if not policy.allow_auto_approve_on_unknown
                else SC_UNKNOWN_FIELD
            )
            assessment.hits.append(
                SafetyHit(
                    code=code,
                    reason=f"Critical field '{name}' is UNKNOWN",
                    preferred_decision=DecisionKind.HUMAN_REVIEW,
                )
            )
        elif field.presence == FieldPresence.AMBIGUOUS:
            assessment.hits.append(
                SafetyHit(
                    code=SC_AMBIGUOUS_FIELD,
                    reason=f"Critical field '{name}' is AMBIGUOUS",
                    preferred_decision=DecisionKind.HUMAN_REVIEW,
                )
            )
        elif field.presence == FieldPresence.KNOWN:
            if not field.evidence:
                assessment.hits.append(
                    SafetyHit(
                        code=SC_MISSING_EVIDENCE,
                        reason=f"Critical field '{name}' lacks evidence",
                        preferred_decision=DecisionKind.HUMAN_REVIEW,
                    )
                )
            conf = field.confidence
            if conf is None or conf < policy.high_confidence_threshold:
                assessment.hits.append(
                    SafetyHit(
                        code=SC_LOW_CONFIDENCE,
                        reason=(
                            f"Critical field '{name}' confidence "
                            f"{conf!s} below threshold {policy.high_confidence_threshold}"
                        ),
                        preferred_decision=DecisionKind.HUMAN_REVIEW,
                    )
                )
            if field.uncertainty == UncertaintyFlag.CONFLICTING_EVIDENCE:
                assessment.hits.append(
                    SafetyHit(
                        code=SC_CONFLICTING_EVIDENCE,
                        reason=f"Critical field '{name}' has conflicting evidence",
                        preferred_decision=DecisionKind.HUMAN_REVIEW,
                    )
                )
            elif field.uncertainty not in {UncertaintyFlag.NONE}:
                assessment.hits.append(
                    SafetyHit(
                        code=SC_LOW_CONFIDENCE,
                        reason=f"Critical field '{name}' carries uncertainty={field.uncertainty}",
                        preferred_decision=DecisionKind.HUMAN_REVIEW,
                    )
                )

    return assessment
