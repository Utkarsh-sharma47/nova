"""Structured logging for document processing (never logs document contents)."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from nova.observability.metrics import observe_document_processing

logger = logging.getLogger("nova.documents")

_STAGE = "document_processing"


def _extra(
    *,
    event: str,
    status: str,
    document_id: UUID | None,
    trace_id: UUID | None,
    processor_version: str,
    duration_ms: float | None = None,
    error_code: str | None = None,
    **fields: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event": event,
        "status": status,
        "extra_fields": {
            "stage": _STAGE,
            "processor_version": processor_version,
            **fields,
        },
    }
    if document_id is not None:
        payload["extra_fields"]["document_id"] = str(document_id)
    if trace_id is not None:
        payload["trace_id"] = str(trace_id)
    if duration_ms is not None:
        payload["duration_ms"] = round(duration_ms, 3)
    if error_code is not None:
        payload["error_code"] = error_code
    return payload


def log_processing_start(
    *,
    document_id: UUID,
    trace_id: UUID | None,
    processor_version: str,
    byte_size: int,
    media_type: str,
) -> None:
    observe_document_processing(stage=_STAGE, status="STARTED")
    logger.info(
        "document_processing_start",
        extra=_extra(
            event="document.processing.start",
            status="STARTED",
            document_id=document_id,
            trace_id=trace_id,
            processor_version=processor_version,
            byte_size=byte_size,
            media_type=media_type,
        ),
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
    observe_document_processing(stage=_STAGE, status=status)
    logger.info(
        "document_processing_complete",
        extra=_extra(
            event="document.processing.complete",
            status=status,
            document_id=document_id,
            trace_id=trace_id,
            processor_version=processor_version,
            duration_ms=duration_ms,
            media_type=media_type,
            page_count=page_count,
        ),
    )


def log_processing_failure(
    *,
    document_id: UUID,
    trace_id: UUID | None,
    processor_version: str,
    error_code: str,
    duration_ms: float,
) -> None:
    observe_document_processing(stage=_STAGE, status="FAILED", error_code=error_code)
    logger.warning(
        "document_processing_failure",
        extra=_extra(
            event="document.processing.failure",
            status="FAILED",
            document_id=document_id,
            trace_id=trace_id,
            processor_version=processor_version,
            duration_ms=duration_ms,
            error_code=error_code,
        ),
    )
