"""Normalized document processing request/result models."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from nova.contracts.common import ContractModel, DocumentContent


class ProcessingStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class DocumentSourceMetadata(ContractModel):
    original_filename: str | None = None
    sanitized_filename: str | None = None
    declared_media_type: str | None = None
    detected_media_type: str
    byte_size: int = Field(ge=0)
    content_sha256: str = Field(min_length=64, max_length=64)
    page_count: int | None = Field(default=None, ge=0)
    storage_uri: str | None = None


class DocumentProcessingRequest(ContractModel):
    document_id: UUID
    blob: bytes
    document_type: str | None = Field(
        default=None,
        description="Caller hint only; not inferred business meaning.",
    )
    declared_media_type: str | None = None
    original_filename: str | None = None
    storage_uri: str | None = None
    trace_id: UUID | None = None
    request_id: UUID | None = None


class DocumentProcessingResult(ContractModel):
    document_id: UUID
    document_type: str | None = None
    status: ProcessingStatus
    content: DocumentContent | None = None
    source: DocumentSourceMetadata
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    processor_version: str
    duration_ms: float | None = Field(default=None, ge=0)
    trace_id: UUID | None = None
    request_id: UUID | None = None
