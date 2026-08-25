"""Decision persistence with failsafe boundary checks."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from nova.contracts.routing import DecisionActorType, DecisionKind, DecisionResult
from nova.persistence.models import DecisionRecord


class FailsafeAutoApproveError(ValueError):
    """Raised when system_failsafe attempts to store AUTO_APPROVE."""


def assert_failsafe_cannot_auto_approve(decision: DecisionResult) -> None:
    if (
        decision.actor_type == DecisionActorType.SYSTEM_FAILSAFE
        and decision.decision == DecisionKind.AUTO_APPROVE
    ):
        raise FailsafeAutoApproveError("system_failsafe cannot store AUTO_APPROVE")


def decision_to_record(decision: DecisionResult) -> DecisionRecord:
    assert_failsafe_cannot_auto_approve(decision)
    run_id = decision.verification_run_id or decision.run_id
    if run_id is None:
        raise ValueError("verification_run_id / run_id required to persist decision")
    return DecisionRecord(
        decision_id=uuid4(),
        verification_run_id=run_id,
        shipment_id=decision.shipment_id,
        document_id=decision.document_id,
        document_version_id=decision.document_version_id,
        validation_result_id=decision.validation_result_id,
        disposition=decision.decision.value,
        policy_id=decision.policy_id,
        policy_version=decision.policy_version,
        reason_codes=list(decision.reason_codes),
        reasons=list(decision.reasons),
        triggering_check_ids=list(decision.triggering_check_ids),
        safety_constraints_applied=list(decision.safety_constraints_applied),
        confidence=decision.confidence,
        actor_type=decision.actor_type.value,
        agent_version=decision.agent_version,
        trace_id=decision.trace_id,
        reasoning_json={
            "reason_codes": decision.reason_codes,
            "safety_constraints_applied": decision.safety_constraints_applied,
            "llm_overridden": decision.llm_overridden,
            "unsafe_llm_attempt": decision.unsafe_llm_attempt,
        },
        risk_flags=list(decision.safety_constraints_applied) or None,
        supersedes_decision_id=decision.supersedes_decision_id,
        decided_at=decision.completed_at,
        input_fingerprint=decision.input_fingerprint,
        llm_rationale=decision.llm_rationale,
        evidence_refs=list(decision.evidence_refs),
        routing_rule_version=decision.routing_rule_version,
    )


class DecisionRepository:
    """Append-only decision writes. One row per verification_run_id."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_run(self, verification_run_id: object) -> DecisionRecord | None:
        return self.find_by_run(verification_run_id)

    def find_by_run(self, verification_run_id: object) -> DecisionRecord | None:
        from sqlalchemy import select

        return self.session.scalar(
            select(DecisionRecord).where(
                DecisionRecord.verification_run_id == verification_run_id
            )
        )

    def persist(self, decision: DecisionResult) -> DecisionRecord:
        assert_failsafe_cannot_auto_approve(decision)
        existing = self.find_by_run(decision.verification_run_id)
        if existing is not None:
            if existing.input_fingerprint == decision.input_fingerprint:
                return existing
            raise ValueError(
                "contradictory decision for verification run; use a new run_id"
            )
        record = decision_to_record(decision)
        self.session.add(record)
        self.session.flush()
        return record
