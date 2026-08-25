"""Shared contract primitives.

Identity mapping (normative):
- `run_id` — verification run / pipeline correlation (agent + API + DB `verification_run_id`)
- `trace_id` — observability correlation (logs/traces); may equal run_id in Part 1 demos
- Entity IDs — UUID strings at persistence; UUID in Pydantic stage contracts
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContractModel(BaseModel):
    """Base for all Nova contracts."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class FieldPresence(StrEnum):
    """Whether a value is available and how it was obtained (agent semantic SoT)."""

    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    MISSING = "MISSING"
    AMBIGUOUS = "AMBIGUOUS"


class UncertaintyFlag(StrEnum):
    """Residual doubt orthogonal to FieldPresence."""

    NONE = "NONE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    PARTIAL_EVIDENCE = "PARTIAL_EVIDENCE"
    SCHEMA_REPAIR = "SCHEMA_REPAIR"
    OTHER = "OTHER"


class UncertaintyCode(StrEnum):
    """Backward-compatible multi-code list used alongside UncertaintyFlag."""

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


class EvidenceSourceType(StrEnum):
    DOCUMENT_SPAN = "DOCUMENT_SPAN"
    OCR_BLOCK = "OCR_BLOCK"
    TABLE_CELL = "TABLE_CELL"
    DERIVED = "DERIVED"
    NONE = "NONE"


class EvidenceType(StrEnum):
    """Compatibility aliases for Evidence.source_type mapping."""

    SNIPPET = "SNIPPET"
    PAGE_REGION = "PAGE_REGION"
    PAGE_REF = "PAGE_REF"
    NONE = "NONE"


class Evidence(ContractModel):
    evidence_id: str | None = None
    document_id: UUID | None = None
    source_type: EvidenceSourceType = EvidenceSourceType.NONE
    # Compatibility field used by earlier drafts
    evidence_type: EvidenceType = EvidenceType.NONE
    snippet: str | None = None
    page: int | None = Field(default=None, ge=1)
    page_number: int | None = Field(default=None, ge=1)
    bbox: list[float] | None = Field(
        default=None,
        description="Optional region; prefer [x0,y0,x1,y1] or [x,y,w,h] documented per processor",
    )
    locator: str | None = None
    processor_ref: str | None = None
    notes: str | None = None


class UsageMetrics(ContractModel):
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    latency_ms: int | None = Field(default=None, ge=0)
    attempt: int | None = Field(default=None, ge=1)


class ModelMetadata(ContractModel):
    """Model/prompt invocation metadata (maps to agent ModelInvocationMetadata)."""

    provider: str | None = None
    model: str | None = None
    prompt_id: str | None = None
    prompt_version: str | None = None
    agent_version: str | None = None
    temperature: float | None = None
    other_config: dict[str, Any] | None = None
    invoked_at: datetime | None = None


class DocumentImage(ContractModel):
    """Inline image payload for vision-capable LLM adapters (not logged as body)."""

    media_type: str
    data_base64: str = Field(min_length=1)


class DocumentContent(ContractModel):
    """Normalized document content produced by DocumentProcessorPort."""

    media_type: str
    text: str | None = None
    page_texts: list[str] | None = None
    images: list[DocumentImage] = Field(default_factory=list)
    layout: dict[str, Any] | None = None
    processor_name: str
    processor_version: str
    warnings: list[str] = Field(default_factory=list)


class TraceContext(ContractModel):
    contract_version: str = "1.0.0"
    run_id: UUID | None = Field(
        default=None,
        description="Verification run ID; equals DB verification_run_id",
    )
    trace_id: UUID
    request_id: UUID | None = None
    agent_execution_id: UUID | None = None
    document_id: UUID | None = None
    document_version_id: UUID | None = None
    shipment_id: UUID | None = None
    customer_id: UUID | None = None
    created_at: datetime | None = None


class StageError(ContractModel):
    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] | None = None
