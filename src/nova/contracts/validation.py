"""Validation stage contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from nova.contracts.common import ModelMetadata, TraceContext, UsageMetrics
from nova.contracts.extraction import ExtractedField


class ValidationOutcome(StrEnum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    UNCERTAIN = "UNCERTAIN"


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
    outcome: ValidationOutcome
    reason: str
    details: dict[str, Any] | None = None


class ValidationRequest(TraceContext):
    document_id: UUID
    document_version_id: UUID
    shipment_id: UUID
    customer_id: UUID
    extraction_result_id: UUID
    rules: list[CustomerRuleSnapshot] = Field(min_length=1)
    extracted_fields: list[ExtractedField]
    related_extractions: list[list[ExtractedField]] = Field(
        default_factory=list,
        description="Reserved for Part 2 cross-document validation",
    )


class ValidationResult(TraceContext):
    document_id: UUID
    document_version_id: UUID
    shipment_id: UUID
    extraction_result_id: UUID
    checks: list[ValidationCheck] = Field(default_factory=list)
    match_count: int = Field(default=0, ge=0)
    mismatch_count: int = Field(default=0, ge=0)
    uncertain_count: int = Field(default=0, ge=0)
    engine_version: str
    model_metadata: ModelMetadata | None = None
    usage: UsageMetrics | None = None
    error_code: str | None = None
    error_message: str | None = None
