"""Routing / decision contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from nova.contracts.common import ModelMetadata, StageError, TraceContext, UsageMetrics
from nova.contracts.validation import ValidationOutcome, ValidationResult


class DecisionKind(StrEnum):
    AUTO_APPROVE = "AUTO_APPROVE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    AMENDMENT_REQUEST = "AMENDMENT_REQUEST"


class RoutingPolicySnapshot(TraceContext):
    policy_id: str
    policy_version: str
    high_confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    low_confidence_threshold: float = Field(default=0.60, ge=0.0, le=1.0)
    allow_auto_approve_on_unknown: bool = Field(
        default=False,
        description="Part 1 hard default is False; must never be silently enabled",
    )
    extra: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _threshold_order(self) -> RoutingPolicySnapshot:
        if self.low_confidence_threshold > self.high_confidence_threshold:
            raise ValueError("low_confidence_threshold cannot exceed high_confidence_threshold")
        return self


class RoutingRequest(TraceContext):
    document_id: UUID
    document_version_id: UUID
    shipment_id: UUID
    validation_result_id: UUID
    validation: ValidationResult
    policy: RoutingPolicySnapshot
    blocking_uncertainty_present: bool = False
    timeout_ms: int = Field(default=15_000, ge=1)


class DecisionResult(TraceContext):
    document_id: UUID
    document_version_id: UUID
    shipment_id: UUID
    validation_result_id: UUID
    decision: DecisionKind
    reasons: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    triggering_check_ids: list[UUID] = Field(default_factory=list)
    policy_id: str | None = None
    policy_version: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    safety_constraints_applied: list[str] = Field(default_factory=list)
    requires_human_attention: bool
    supersedes_decision_id: UUID | None = None
    errors: list[StageError] = Field(default_factory=list)
    model_metadata: ModelMetadata | None = None
    usage: UsageMetrics | None = None
    llm_rationale: str | None = Field(
        default=None,
        description="Non-authoritative explanation; policy decision is authoritative",
    )

    @model_validator(mode="after")
    def _auto_approve_safety(self) -> DecisionResult:
        if self.decision == DecisionKind.AUTO_APPROVE:
            if self.requires_human_attention:
                raise ValueError("AUTO_APPROVE cannot set requires_human_attention=true")
        else:
            object.__setattr__(self, "requires_human_attention", True)
        return self


def validation_blocks_auto_approve(validation: ValidationResult) -> bool:
    """Deterministic helper: any MISMATCH/UNCERTAIN blocks AUTO_APPROVE."""
    return any(
        c.outcome in {ValidationOutcome.MISMATCH, ValidationOutcome.UNCERTAIN}
        for c in validation.checks
    )
