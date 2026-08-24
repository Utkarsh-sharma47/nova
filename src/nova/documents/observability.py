"""Structured logging for document processing (never logs document contents)."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

logger = logging.getLogger("nova.documents")


def _base_fields(
    *,
    document_id: UUID | None,
    trace_id: UUID | None,
    processor_version: str,
    **extra: Any,
) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "stage": "document_processing",
        "processor_version": processor_version,
    }
    if document_id is not None:
        fields["document_id"] = str(document_id)
    if trace_id is not None:
        fields["trace_id"] = str(trace_id)
    fields.update(extra)
    return fields


def log_processing_start(
    *,
    document_id: UUID,
    trace_id: UUID | None,
    processor_version: str,
    byte_size: int,
    media_type: str,
) -> None:
    logger.info(
        "document_processing_start",
        extra={
            "nova": _base_fields(
                document_id=document_id,
                trace_id=trace_id,
                processor_version=processor_version,
                status="STARTED",
                byte_size=byte_size,
                media_type=media_type,
            )
        },
    )


def log_processing_complete(
    *,
    document_id: UUID,
    trace_id: UUID | None,
    processor_version: str,
    status: str,
    duration_ms: float,
    media_type: str,
    page_count: int | None = None,
) -> None:
    logger.info(
        "document_processing_complete",
        extra={
            "nova": _base_fields(
                document_id=document_id,
                trace_id=trace_id,
                processor_version=processor_version,
                status=status,
                duration_ms=round(duration_ms, 3),
                media_type=media_type,
                page_count=page_count,
            )
        },
    )


def log_processing_failure(
    *,
    document_id: UUID,
    trace_id: UUID | None,
    processor_version: str,
    error_code: str,
    duration_ms: float,
) -> None:
    logger.warning(
        "document_processing_failure",
        extra={
            "nova": _base_fields(
                document_id=document_id,
                trace_id=trace_id,
                processor_version=processor_version,
                status="FAILED",
                error_code=error_code,
                duration_ms=round(duration_ms, 3),
            )
        },
    )
