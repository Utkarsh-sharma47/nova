"""Validation stage contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from nova.contracts.common import Evidence, ModelMetadata, StageError, TraceContext, UsageMetrics
from nova.contracts.extraction import ExtractedField


class ValidationOutcome(StrEnum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    UNCERTAIN = "UNCERTAIN"


class ValidationStatus(StrEnum):
    """Stage-level status (distinct from per-check outcomes)."""

    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CustomerRuleSnapshot(TraceContext):
    rule_id: UUID
    rule_code: str
    version: str
    severity: str
    blocking: bool = True
    requires_judgment: bool = False
    expression: dict[str, Any] = Field(default_factory=dict)


class ValidationCheck(TraceContext):
    rule_id: UUID
    rule_code: str
    field_name: str | None = None
    expected_value: Any | None = None
    actual_value: Any | None = None
    outcome: ValidationOutcome  # agent docs may call this `result`
    reason: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)
    deterministic: bool = True
    severity: str | None = None
    details: dict[str, Any] | None = None


class ValidationRequest(TraceContext):
    document_id: UUID
    document_version_id: UUID
    shipment_id: UUID
    customer_id: UUID
    extraction_result_id: UUID | None = None
    ruleset_id: str | None = None
    ruleset_version: str | None = None
    rules: list[CustomerRuleSnapshot] = Field(min_length=1)
    extracted_fields: list[ExtractedField]
    related_extractions: list[list[ExtractedField]] = Field(
        default_factory=list,
        description="Reserved for Part 2 cross-document validation",
    )
    timeout_ms: int = Field(default=30_000, ge=1)
    # Optional extraction status for fail-closed invalid extraction handling
    extraction_status: str | None = None


class ValidationResult(TraceContext):
    document_id: UUID
    document_version_id: UUID
    shipment_id: UUID
    extraction_result_id: UUID | None = None
    status: ValidationStatus = ValidationStatus.COMPLETED
    ruleset_id: str | None = None
    ruleset_version: str | None = None
    checks: list[ValidationCheck] = Field(default_factory=list)
    match_count: int = Field(default=0, ge=0)
    mismatch_count: int = Field(default=0, ge=0)
    uncertain_count: int = Field(default=0, ge=0)
    engine_version: str
    warnings: list[str] = Field(default_factory=list)
    errors: list[StageError] = Field(default_factory=list)
    model_metadata: ModelMetadata | None = None
    usage: UsageMetrics | None = None
    error_code: str | None = None
    error_message: str | None = None
