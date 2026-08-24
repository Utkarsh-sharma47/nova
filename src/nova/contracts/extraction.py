"""Extraction stage contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from nova.contracts.common import (
    ConfidenceBand,
    ConfidenceSource,
    DocumentContent,
    Evidence,
    ModelMetadata,
    TraceContext,
    UncertaintyCode,
    UsageMetrics,
)


class ExtractionStatus(StrEnum):
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ExtractedField(TraceContext):
    field_name: str
    value: Any | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_band: ConfidenceBand = ConfidenceBand.UNKNOWN
    confidence_source: ConfidenceSource = ConfidenceSource.UNKNOWN
    evidence: Evidence = Field(default_factory=Evidence)
    uncertainty_codes: list[UncertaintyCode] = Field(default_factory=list)

    @field_validator("uncertainty_codes")
    @classmethod
    def _dedupe_codes(cls, codes: list[UncertaintyCode]) -> list[UncertaintyCode]:
        seen: set[UncertaintyCode] = set()
        out: list[UncertaintyCode] = []
        for code in codes:
            if code not in seen:
                seen.add(code)
                out.append(code)
        return out


class ExtractionRequest(TraceContext):
    document_id: UUID
    document_version_id: UUID
    shipment_id: UUID
    document_type: str
    content: DocumentContent
    required_fields: list[str] = Field(min_length=1)
    customer_hints: dict[str, Any] | None = None


class ExtractionResult(TraceContext):
    document_id: UUID
    document_version_id: UUID
    shipment_id: UUID
    status: ExtractionStatus
    fields: list[ExtractedField] = Field(default_factory=list)
    model_metadata: ModelMetadata | None = None
    usage: UsageMetrics | None = None
    error_code: str | None = None
    error_message: str | None = None
