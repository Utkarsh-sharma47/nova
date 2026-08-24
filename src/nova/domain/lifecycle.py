"""Pure lifecycle policy for Phase 3 entities."""

from __future__ import annotations

from enum import StrEnum

from nova.domain.errors import InvalidLifecycleTransition


class DocumentStatus(StrEnum):
    REGISTERED = "registered"
    CONTENT_AVAILABLE = "content_available"
    IN_PIPELINE = "in_pipeline"
    EXTRACTED = "extracted"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class VerificationRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


_DOCUMENT_TRANSITIONS: dict[DocumentStatus, frozenset[DocumentStatus]] = {
    DocumentStatus.REGISTERED: frozenset(
        {DocumentStatus.CONTENT_AVAILABLE, DocumentStatus.WITHDRAWN}
    ),
    DocumentStatus.CONTENT_AVAILABLE: frozenset(
        {DocumentStatus.IN_PIPELINE, DocumentStatus.SUPERSEDED, DocumentStatus.WITHDRAWN}
    ),
    DocumentStatus.IN_PIPELINE: frozenset(
        {DocumentStatus.EXTRACTED, DocumentStatus.WITHDRAWN}
    ),
    DocumentStatus.EXTRACTED: frozenset(
        {DocumentStatus.SUPERSEDED, DocumentStatus.WITHDRAWN}
    ),
    DocumentStatus.SUPERSEDED: frozenset(),
    DocumentStatus.WITHDRAWN: frozenset(),
}

_RUN_TRANSITIONS: dict[VerificationRunStatus, frozenset[VerificationRunStatus]] = {
    VerificationRunStatus.QUEUED: frozenset(
        {VerificationRunStatus.RUNNING, VerificationRunStatus.CANCELLED}
    ),
    VerificationRunStatus.RUNNING: frozenset(
        {
            VerificationRunStatus.SUCCEEDED,
            VerificationRunStatus.FAILED,
            VerificationRunStatus.CANCELLED,
        }
    ),
    VerificationRunStatus.SUCCEEDED: frozenset(),
    VerificationRunStatus.FAILED: frozenset(),
    VerificationRunStatus.CANCELLED: frozenset(),
}


def assert_document_transition(
    current: DocumentStatus,
    target: DocumentStatus,
) -> None:
    if target not in _DOCUMENT_TRANSITIONS[current]:
        raise InvalidLifecycleTransition(
            details={"entity": "document", "from": current, "to": target}
        )


def assert_run_transition(
    current: VerificationRunStatus,
    target: VerificationRunStatus,
) -> None:
    if target not in _RUN_TRANSITIONS[current]:
        raise InvalidLifecycleTransition(
            details={"entity": "verification_run", "from": current, "to": target}
        )
