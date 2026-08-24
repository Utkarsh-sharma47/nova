"""Domain enums and lifecycle rules."""

from __future__ import annotations

from enum import StrEnum


class CustomerStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class ShipmentStatus(StrEnum):
    OPEN = "open"
    INGESTING = "ingesting"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    ROUTING = "routing"
    DECIDED = "decided"
    CLOSED = "closed"


class DocumentStatus(StrEnum):
    """Phase 3 document lifecycle."""

    RECEIVED = "received"
    STORED = "stored"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class DocumentType(StrEnum):
    COMMERCIAL_INVOICE = "commercial_invoice"
    BILL_OF_LADING = "bill_of_lading"
    PACKING_LIST = "packing_list"
    OTHER = "other"


class IngestionChannel(StrEnum):
    UPLOAD = "upload"
    PATH = "path"
    EMAIL = "email"
    API = "api"


class VerificationRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ApiDocumentStatus(StrEnum):
    """Wire status values from docs/api/contracts.md."""

    ACCEPTED = "ACCEPTED"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    VALIDATED = "VALIDATED"
    DECIDED = "DECIDED"
    FAILED = "FAILED"


DOCUMENT_TRANSITIONS: dict[DocumentStatus, frozenset[DocumentStatus]] = {
    DocumentStatus.RECEIVED: frozenset(
        {DocumentStatus.STORED, DocumentStatus.FAILED, DocumentStatus.WITHDRAWN}
    ),
    DocumentStatus.STORED: frozenset(
        {
            DocumentStatus.PROCESSING,
            DocumentStatus.FAILED,
            DocumentStatus.WITHDRAWN,
            DocumentStatus.SUPERSEDED,
        }
    ),
    DocumentStatus.PROCESSING: frozenset(
        {DocumentStatus.PROCESSED, DocumentStatus.FAILED, DocumentStatus.SUPERSEDED}
    ),
    DocumentStatus.PROCESSED: frozenset({DocumentStatus.SUPERSEDED, DocumentStatus.WITHDRAWN}),
    DocumentStatus.FAILED: frozenset({DocumentStatus.WITHDRAWN}),
    DocumentStatus.SUPERSEDED: frozenset(),
    DocumentStatus.WITHDRAWN: frozenset(),
}


class InvalidDocumentTransitionError(ValueError):
    def __init__(self, current: DocumentStatus, new: DocumentStatus) -> None:
        self.current = current
        self.new = new
        super().__init__(f"Invalid document status transition: {current} → {new}")


def assert_document_transition(current: DocumentStatus, new: DocumentStatus) -> None:
    allowed = DOCUMENT_TRANSITIONS.get(current, frozenset())
    if new not in allowed:
        raise InvalidDocumentTransitionError(current, new)


WIRE_DOCUMENT_TYPE: dict[str, DocumentType] = {
    "INVOICE": DocumentType.COMMERCIAL_INVOICE,
    "COMMERCIAL_INVOICE": DocumentType.COMMERCIAL_INVOICE,
    "BILL_OF_LADING": DocumentType.BILL_OF_LADING,
    "PACKING_LIST": DocumentType.PACKING_LIST,
    "OTHER": DocumentType.OTHER,
    "UNKNOWN": DocumentType.OTHER,
}


def parse_wire_document_type(value: str | None) -> DocumentType:
    if value is None or value.strip() == "":
        return DocumentType.OTHER
    key = value.strip().upper()
    if key in WIRE_DOCUMENT_TYPE:
        return WIRE_DOCUMENT_TYPE[key]
    lower = value.strip().lower()
    try:
        return DocumentType(lower)
    except ValueError as exc:
        raise ValueError(f"Unsupported document_type: {value}") from exc


def to_api_status(status: DocumentStatus) -> ApiDocumentStatus:
    mapping = {
        DocumentStatus.RECEIVED: ApiDocumentStatus.ACCEPTED,
        DocumentStatus.STORED: ApiDocumentStatus.ACCEPTED,
        DocumentStatus.PROCESSING: ApiDocumentStatus.PROCESSING,
        DocumentStatus.PROCESSED: ApiDocumentStatus.EXTRACTED,
        DocumentStatus.FAILED: ApiDocumentStatus.FAILED,
        DocumentStatus.SUPERSEDED: ApiDocumentStatus.FAILED,
        DocumentStatus.WITHDRAWN: ApiDocumentStatus.FAILED,
    }
    return mapping[status]
