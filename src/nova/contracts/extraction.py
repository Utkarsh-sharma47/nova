"""Extraction stage contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from nova.contracts.common import (
    ConfidenceBand,
    ConfidenceSource,
    DocumentContent,
    Evidence,
    FieldPresence,
    ModelMetadata,
    StageError,
    TraceContext,
    UncertaintyCode,
    UncertaintyFlag,
    UsageMetrics,
)


class ExtractionStatus(StrEnum):
    """Wire values. SUCCEEDED is canonical; COMPLETED retained as alias input."""

    SUCCEEDED = "SUCCEEDED"
    COMPLETED = "COMPLETED"  # accepted on input; normalize to SUCCEEDED in validators if needed
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ExtractedField(TraceContext):
    field_name: str = Field(description="Canonical field name (agent: name)")
    value: Any | None = None
    value_type: str = "string"
    presence: FieldPresence = FieldPresence.UNKNOWN
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_band: ConfidenceBand = ConfidenceBand.UNKNOWN
    confidence_source: ConfidenceSource = ConfidenceSource.UNKNOWN
    uncertainty: UncertaintyFlag = UncertaintyFlag.NONE
    uncertainty_codes: list[UncertaintyCode] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    source_location: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    candidates: list[dict[str, Any]] | None = None

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

    @model_validator(mode="after")
    def _presence_value_invariant(self) -> ExtractedField:
        if self.presence != FieldPresence.KNOWN and self.value is not None:
            raise ValueError(
                f"presence={self.presence} requires value=null (got non-null value)"
            )
        if self.presence == FieldPresence.KNOWN and self.value is None:
            raise ValueError("presence=KNOWN requires a non-null value")
        if self.presence == FieldPresence.KNOWN and not self.evidence:
            raise ValueError("presence=KNOWN requires at least one evidence entry")
        if self.confidence is None and self.uncertainty == UncertaintyFlag.NONE:
            if self.presence == FieldPresence.KNOWN:
                raise ValueError(
                    "KNOWN fields must provide confidence or an uncertainty flag"
                )
        return self


class ExtractionRequest(TraceContext):
    document_id: UUID
    document_version_id: UUID
    shipment_id: UUID
    customer_id: UUID | None = None
    document_type: str | None = None
    content: DocumentContent | None = None
    document_ref: dict[str, Any] | None = Field(
        default=None,
        description="Storage handle when content is not embedded",
    )
    required_fields: list[str] = Field(min_length=1)
    customer_hints: dict[str, Any] | None = None
    timeout_ms: int = Field(default=60_000, ge=1)
    locale: str | None = None

    @model_validator(mode="after")
    def _content_or_ref(self) -> ExtractionRequest:
        if self.content is None and self.document_ref is None:
            raise ValueError("either content or document_ref is required")
        return self


class ExtractionResult(TraceContext):
    document_id: UUID
    document_version_id: UUID
    shipment_id: UUID
    status: ExtractionStatus
    fields: list[ExtractedField] = Field(default_factory=list)
    document_type_detected: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[StageError] = Field(default_factory=list)
    model_metadata: ModelMetadata | None = None
    usage: UsageMetrics | None = None
    error_code: str | None = None
    error_message: str | None = None

    @model_validator(mode="after")
    def _normalize_status(self) -> ExtractionResult:
        if self.status == ExtractionStatus.COMPLETED:
            object.__setattr__(self, "status", ExtractionStatus.SUCCEEDED)
        if self.status == ExtractionStatus.FAILED and not self.errors and not self.error_code:
            raise ValueError("FAILED extraction requires errors or error_code")
        return self
