"""Routing / decision contracts.

Aligns runtime shapes with docs/agents/contracts.md Router section while
preserving Phase 2 Pydantic field names already used in the codebase.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from nova.contracts.common import ModelMetadata, StageError, TraceContext, UsageMetrics
from nova.contracts.extraction import ExtractionResult
from nova.contracts.validation import ValidationOutcome, ValidationResult


class DecisionKind(StrEnum):
    AUTO_APPROVE = "AUTO_APPROVE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    AMENDMENT_REQUEST = "AMENDMENT_REQUEST"


class DecisionActorType(StrEnum):
    """Who produced the decision (maps to DB actor_type)."""

    ROUTER = "router"
    SYSTEM_FAILSAFE = "system_failsafe"


class LlmRoutingSuggestion(TraceContext):
    """Optional advisory LLM output. Never authoritative for AUTO_APPROVE."""

    available: bool = True
    malformed: bool = False
    decision: DecisionKind | None = None
    rationale: str | None = None
    triggering_check_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    fabricated_evidence: bool = False
    raw_payload: dict[str, Any] | None = None


class RoutingPolicySnapshot(TraceContext):
    policy_id: str
    policy_version: str
    high_confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    low_confidence_threshold: float = Field(default=0.60, ge=0.0, le=1.0)
    allow_auto_approve_on_unknown: bool = Field(
        default=False,
        description="Part 1 hard default is False; must never be silently enabled",
    )
    critical_fields: list[str] = Field(
        default_factory=list,
        description="Fields that must be KNOWN for AUTO_APPROVE eligibility",
    )
    blocking_mismatch_decision: DecisionKind = Field(
        default=DecisionKind.AMENDMENT_REQUEST,
        description="Disposition when a blocking MISMATCH is present",
    )
    blocking_uncertain_decision: DecisionKind = Field(
        default=DecisionKind.HUMAN_REVIEW,
        description="Disposition when a blocking UNCERTAIN is present",
    )
    require_evidence_for_auto_approve: bool = True
    min_decision_confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    extra: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _threshold_order(self) -> RoutingPolicySnapshot:
        if self.low_confidence_threshold > self.high_confidence_threshold:
            raise ValueError("low_confidence_threshold cannot exceed high_confidence_threshold")
        if self.blocking_mismatch_decision == DecisionKind.AUTO_APPROVE:
            raise ValueError("blocking_mismatch_decision cannot be AUTO_APPROVE")
        if self.blocking_uncertain_decision == DecisionKind.AUTO_APPROVE:
            raise ValueError("blocking_uncertain_decision cannot be AUTO_APPROVE")
        return self


class RoutingRequest(TraceContext):
    document_id: UUID
    document_version_id: UUID
    shipment_id: UUID
    verification_run_id: UUID
    validation_result_id: UUID
    extraction: ExtractionResult
    validation: ValidationResult
    policy: RoutingPolicySnapshot
    blocking_uncertainty_present: bool = False
    timeout_ms: int = Field(default=15_000, ge=1)
    correlation: dict[str, Any] | None = None
    llm_suggestion: LlmRoutingSuggestion | None = None


class DecisionResult(TraceContext):
    document_id: UUID
    document_version_id: UUID
    shipment_id: UUID
    verification_run_id: UUID
    validation_result_id: UUID
    decision: DecisionKind
    reasons: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    triggering_check_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    policy_id: str
    policy_version: str
    routing_rule_version: str
    agent_version: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    safety_constraints_applied: list[str] = Field(default_factory=list)
    requires_human_attention: bool
    actor_type: DecisionActorType = DecisionActorType.ROUTER
    input_fingerprint: str
    supersedes_decision_id: UUID | None = None
    model_metadata: ModelMetadata | None = None
    usage: UsageMetrics | None = None
    llm_rationale: str | None = Field(
        default=None,
        description="Non-authoritative explanation; policy decision is authoritative",
    )
    llm_overridden: bool = False
    unsafe_llm_attempt: bool = Field(
        default=False,
        description="True when an LLM suggested AUTO_APPROVE that safety rejected",
    )
    completed_at: datetime
    errors: list[StageError] = Field(default_factory=list)

    @model_validator(mode="after")
    def _auto_approve_safety(self) -> DecisionResult:
        if self.decision == DecisionKind.AUTO_APPROVE:
            if self.actor_type == DecisionActorType.SYSTEM_FAILSAFE:
                raise ValueError("system_failsafe cannot emit AUTO_APPROVE")
            if self.safety_constraints_applied:
                raise ValueError("AUTO_APPROVE forbidden when safety constraints applied")
            if self.requires_human_attention:
                raise ValueError("AUTO_APPROVE cannot set requires_human_attention=true")
            object.__setattr__(self, "requires_human_attention", False)
        else:
            object.__setattr__(self, "requires_human_attention", True)
        return self


def validation_blocks_auto_approve(validation: ValidationResult) -> bool:
    """Deterministic helper: any MISMATCH/UNCERTAIN blocks AUTO_APPROVE."""
    return any(
        c.outcome in {ValidationOutcome.MISMATCH, ValidationOutcome.UNCERTAIN}
        for c in validation.checks
    )
