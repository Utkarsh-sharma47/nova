"""Contract tests for DecisionResult AUTO_APPROVE invariants."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from nova.contracts.routing import DecisionActorType, DecisionKind, DecisionResult


def test_auto_approve_rejects_failsafe_actor() -> None:
    with pytest.raises(ValidationError):
        DecisionResult(
            trace_id=uuid4(),
            document_id=uuid4(),
            document_version_id=uuid4(),
            shipment_id=uuid4(),
            verification_run_id=uuid4(),
            validation_result_id=uuid4(),
            decision=DecisionKind.AUTO_APPROVE,
            policy_id="p",
            policy_version="1",
            routing_rule_version="r",
            agent_version="a",
            requires_human_attention=False,
            actor_type=DecisionActorType.SYSTEM_FAILSAFE,
            input_fingerprint="x",
            completed_at=datetime.now(UTC),
        )


def test_auto_approve_rejects_safety_constraints() -> None:
    with pytest.raises(ValidationError):
        DecisionResult(
            trace_id=uuid4(),
            document_id=uuid4(),
            document_version_id=uuid4(),
            shipment_id=uuid4(),
            verification_run_id=uuid4(),
            validation_result_id=uuid4(),
            decision=DecisionKind.AUTO_APPROVE,
            policy_id="p",
            policy_version="1",
            routing_rule_version="r",
            agent_version="a",
            requires_human_attention=False,
            safety_constraints_applied=["SC_BLOCKING_MISMATCH"],
            input_fingerprint="x",
            completed_at=datetime.now(UTC),
        )
