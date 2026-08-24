"""Extractor observability — never log document bodies, secrets, or full prompts."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

logger = logging.getLogger("nova.extraction")


def _log(event: str, message: str, level: int = logging.INFO, **fields: Any) -> None:
    safe = {
        key: value
        for key, value in fields.items()
        if key
        not in {
            "document_body",
            "prompt",
            "full_prompt",
            "api_key",
            "text",
            "content",
            "messages",
        }
    }
    logger.log(
        level,
        message,
        extra={
            "event": event,
            "extra_fields": safe,
        },
    )


def log_start(
    *,
    run_id: UUID,
    document_id: UUID,
    trace_id: UUID,
    agent_execution_id: UUID,
    prompt_version: str,
    provider: str,
    model: str,
) -> None:
    _log(
        "extractor.start",
        "extractor_execution_start",
        run_id=str(run_id),
        document_id=str(document_id),
        trace_id=str(trace_id),
        agent_execution_id=str(agent_execution_id),
        prompt_version=prompt_version,
        provider=provider,
        model=model,
        stage="extractor",
        status="STARTED",
    )


def log_complete(
    *,
    run_id: UUID,
    document_id: UUID,
    trace_id: UUID,
    agent_execution_id: UUID,
    prompt_version: str,
    provider: str,
    model: str,
    status: str,
    duration_ms: float,
    attempt: int,
) -> None:
    _log(
        "extractor.complete",
        "extractor_execution_complete",
        run_id=str(run_id),
        document_id=str(document_id),
        trace_id=str(trace_id),
        agent_execution_id=str(agent_execution_id),
        prompt_version=prompt_version,
        provider=provider,
        model=model,
        stage="extractor",
        status=status,
        duration_ms=round(duration_ms, 3),
        attempt=attempt,
    )


def log_failure(
    *,
    run_id: UUID,
    document_id: UUID,
    trace_id: UUID,
    agent_execution_id: UUID,
    prompt_version: str,
    provider: str,
    model: str,
    error_code: str,
    duration_ms: float,
    attempt: int,
) -> None:
    _log(
        "extractor.failure",
        "extractor_execution_failure",
        level=logging.WARNING,
        run_id=str(run_id),
        document_id=str(document_id),
        trace_id=str(trace_id),
        agent_execution_id=str(agent_execution_id),
        prompt_version=prompt_version,
        provider=provider,
        model=model,
        stage="extractor",
        status="FAILED",
        error_code=error_code,
        duration_ms=round(duration_ms, 3),
        attempt=attempt,
    )
