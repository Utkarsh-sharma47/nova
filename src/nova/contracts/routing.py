"""Routing / decision contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from nova.contracts.common import ModelMetadata, TraceContext, UsageMetrics
from nova.contracts.validation import ValidationResult


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


class DecisionResult(TraceContext):
    document_id: UUID
    document_version_id: UUID
    shipment_id: UUID
    validation_result_id: UUID
    decision: DecisionKind
    reasons: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    policy_version: str
    requires_human_attention: bool
    supersedes_decision_id: UUID | None = None
    model_metadata: ModelMetadata | None = None
    usage: UsageMetrics | None = None
    llm_rationale: str | None = Field(
        default=None,
        description="Non-authoritative explanation; policy decision is authoritative",
    )

    @model_validator(mode="after")
    def _auto_approve_safety(self) -> DecisionResult:
        # Contract-level documentation aid: callers must still enforce policy.
        # If reasons include UNKNOWN_TO_APPROVE without explicit policy, prefer review —
        # actual enforcement lives in Router implementation (Phase 4).
        if self.decision == DecisionKind.AUTO_APPROVE:
            self.requires_human_attention = False
        else:
            self.requires_human_attention = True
        return self
