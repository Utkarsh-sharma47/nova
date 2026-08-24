"""Shared contract primitives."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContractModel(BaseModel):
    """Base for all Nova contracts."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class UncertaintyCode(StrEnum):
    NONE = "NONE"
    MISSING = "MISSING"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    AMBIGUOUS = "AMBIGUOUS"
    CONTRADICTORY = "CONTRADICTORY"
    UNSUPPORTED_DOC_TYPE = "UNSUPPORTED_DOC_TYPE"
    UNKNOWN = "UNKNOWN"


class ConfidenceBand(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class ConfidenceSource(StrEnum):
    MODEL = "MODEL"
    HEURISTIC = "HEURISTIC"
    HUMAN = "HUMAN"
    UNKNOWN = "UNKNOWN"


class EvidenceType(StrEnum):
    SNIPPET = "SNIPPET"
    PAGE_REGION = "PAGE_REGION"
    PAGE_REF = "PAGE_REF"
    NONE = "NONE"


class Evidence(ContractModel):
    evidence_type: EvidenceType = EvidenceType.NONE
    snippet: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    bbox: list[float] | None = Field(
        default=None,
        description="Optional normalized [x0,y0,x1,y1] in 0..1",
    )
    processor_ref: str | None = None


class UsageMetrics(ContractModel):
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)


class ModelMetadata(ContractModel):
    provider: str | None = None
    model: str | None = None
    prompt_id: str | None = None
    prompt_version: str | None = None


class DocumentContent(ContractModel):
    """Normalized document content produced by DocumentProcessorPort."""

    media_type: str
    text: str | None = None
    page_texts: list[str] | None = None
    layout: dict[str, Any] | None = None
    processor_name: str
    processor_version: str
    warnings: list[str] = Field(default_factory=list)


class TraceContext(ContractModel):
    contract_version: str = "1.0.0"
    trace_id: UUID
    request_id: UUID | None = None
    agent_execution_id: UUID | None = None
    document_id: UUID | None = None
    document_version_id: UUID | None = None
    shipment_id: UUID | None = None
    customer_id: UUID | None = None
    created_at: datetime | None = None
