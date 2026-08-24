"""Document ingestion use case and read projections."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Never
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nova.documents import (
    DocumentLimits,
    DocumentProcessingRequest,
    DocumentProcessingService,
    ProcessingStatus,
)
from nova.documents.errors import (
    DOC_CORRUPT,
    DOC_EMPTY,
    DOC_INTERNAL,
    DOC_INVALID_FILENAME,
    DOC_MIME_MISMATCH,
    DOC_PATH_TRAVERSAL,
    DOC_PAYLOAD_TOO_LARGE,
    DOC_TOO_MANY_PAGES,
    DOC_UNREADABLE,
    DOC_UNSUPPORTED_EXTENSION,
    DOC_UNSUPPORTED_MEDIA_TYPE,
)
from nova.domain.errors import (
    CustomerNotFound,
    DocumentNotFound,
    DocumentUnreadable,
    ExternalReferenceConflict,
    IdempotencyMismatch,
    NovaError,
    PayloadTooLarge,
    ShipmentNotFound,
    UnsafeFilename,
    UnsupportedMediaType,
    ValidationFailure,
)
from nova.infrastructure.storage import DocumentStoragePort
from nova.persistence.models import (
    Document,
    DocumentVersion,
    IdempotencyRecord,
    Shipment,
    VerificationRun,
)
from nova.persistence.repositories import NovaRepository

logger = logging.getLogger("nova.ingestion")

_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._~-]{8,128}$")
_TYPE_TO_DB = {
    "INVOICE": "commercial_invoice",
    "BILL_OF_LADING": "bill_of_lading",
    "OTHER": "other",
    "UNKNOWN": "other",
}
_TYPE_TO_WIRE = {
    "commercial_invoice": "INVOICE",
    "bill_of_lading": "BILL_OF_LADING",
    "packing_list": "OTHER",
    "other": "OTHER",
}
_STATUS_TO_WIRE = {
    "registered": "ACCEPTED",
    "content_available": "ACCEPTED",
    "in_pipeline": "PROCESSING",
    "extracted": "EXTRACTED",
    "superseded": "FAILED",
    "withdrawn": "FAILED",
}


@dataclass(frozen=True)
class IngestCommand:
    blob: bytes
    filename: str
    media_type: str
    customer_id: UUID
    shipment_id: UUID | None
    document_type: str
    external_ref: str | None
    idempotency_key: str
    principal: str
    trace_id: str


class IngestionService:
    def __init__(
        self,
        session: Session,
        storage: DocumentStoragePort,
        *,
        max_document_size_bytes: int,
        allowed_mime_types: tuple[str, ...],
        processor: DocumentProcessingService | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.max_size = max_document_size_bytes
        self.allowed_mime_types = allowed_mime_types
        self.repository = NovaRepository(session)
        self.processor = processor or DocumentProcessingService(
            limits=DocumentLimits(max_bytes=max_document_size_bytes)
        )

    def load_staged(self, source_path: str) -> tuple[bytes, str, str]:
        filename, blob = self.storage.read_staged(source_path)
        media_type = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".text": "text/plain",
        }.get(Path(filename).suffix.lower(), "application/octet-stream")
        return blob, filename, media_type

    def ingest(self, command: IngestCommand) -> dict[str, Any]:
        if not _KEY_PATTERN.fullmatch(command.idempotency_key):
            raise ValidationFailure(
                "Idempotency-Key must be 8-128 URL-safe characters.",
                details={"field": "Idempotency-Key"},
            )
        document_type = _TYPE_TO_DB.get(command.document_type)
        if document_type is None:
            raise ValidationFailure(
                "Unsupported document_type.",
                details={"document_type": command.document_type},
            )
        content_sha = hashlib.sha256(command.blob).hexdigest()
        principal_hash = hashlib.sha256(command.principal.encode()).hexdigest()
        fingerprint = self._fingerprint(command, content_sha)

        existing = self.repository.idempotency(principal_hash, command.idempotency_key)
        if existing is not None:
            if existing.request_fingerprint != fingerprint:
                raise IdempotencyMismatch()
            replay = dict(existing.response_json)
            replay["idempotent_replay"] = True
            replay["trace_id"] = command.trace_id
            return replay

        document_id = uuid4()
        processing = self.processor.process(
            DocumentProcessingRequest(
                document_id=document_id,
                blob=command.blob,
                document_type=command.document_type,
                declared_media_type=command.media_type,
                original_filename=command.filename,
                trace_id=_as_uuid(command.trace_id),
            )
        )
        if processing.status is ProcessingStatus.FAILED or processing.content is None:
            self._raise_processing_failure(processing.error_code)
        media_type = processing.source.detected_media_type
        if media_type not in self.allowed_mime_types:
            raise UnsupportedMediaType()
        content = processing.content

        storage_uri: str | None = None
        try:
            customer = self.repository.customer(command.customer_id)
            if customer is None or customer.deleted_at is not None or customer.status != "active":
                raise CustomerNotFound(details={"customer_id": str(command.customer_id)})

            if command.external_ref:
                prior = self.repository.document_by_external_ref(
                    command.customer_id,
                    command.external_ref,
                )
                if prior is not None:
                    prior_version = next(
                        (
                            version
                            for version in prior.versions
                            if version.document_version_id == prior.current_version_id
                        ),
                        None,
                    )
                    if prior_version is None or prior_version.content_sha256 != content_sha:
                        raise ExternalReferenceConflict()
                    prior_run = self.repository.run_for_shipment(prior.shipment_id)
                    if prior_run is None:
                        raise RuntimeError("existing document has no verification run")
                    response = self._accepted_response(
                        prior.document_id,
                        prior.shipment_id,
                        prior_run.verification_run_id,
                        command.trace_id,
                        replay=True,
                    )
                    self._record_idempotency(
                        command,
                        principal_hash,
                        fingerprint,
                        response,
                        prior.document_id,
                        prior.shipment_id,
                        prior_run.verification_run_id,
                    )
                    self.session.commit()
                    return response

            shipment = self._resolve_shipment(command)
            version_id = uuid4()
            run_id = uuid4()
            storage_uri = self.storage.put(
                document_id,
                version_id,
                command.filename,
                command.blob,
            )
            document = Document(
                document_id=document_id,
                shipment_id=shipment.shipment_id,
                document_type=document_type,
                status="registered",
                display_name=processing.source.sanitized_filename,
                ingestion_channel="upload",
                external_ref=command.external_ref,
            )
            version = DocumentVersion(
                document_version_id=version_id,
                document_id=document_id,
                shipment_id=shipment.shipment_id,
                document_type=document_type,
                version_number=1,
                storage_uri=storage_uri,
                content_sha256=content_sha,
                media_type=media_type,
                byte_size=len(command.blob),
                original_filename=processing.source.sanitized_filename,
                page_count=processing.source.page_count,
                ingestion_idempotency_key=command.idempotency_key,
                created_by=principal_hash,
                processor_name=content.processor_name,
                processor_version=content.processor_version,
            )
            run = VerificationRun(
                verification_run_id=run_id,
                shipment_id=shipment.shipment_id,
                status="queued",
                idempotency_key=command.idempotency_key,
                trigger="api_upload",
                document_version_ids=[str(version_id)],
            )
            self.repository.add(document)
            self.repository.flush()
            self.repository.add(version)
            self.repository.flush()
            document.current_version_id = version_id
            document.status = "content_available"
            response = self._accepted_response(
                document_id,
                shipment.shipment_id,
                run_id,
                command.trace_id,
                replay=False,
            )
            self.repository.add(run)
            self.repository.flush()
            self._record_idempotency(
                command,
                principal_hash,
                fingerprint,
                response,
                document_id,
                shipment.shipment_id,
                run_id,
            )
            self.session.commit()
            return response
        except IntegrityError as exc:
            self.session.rollback()
            self._cleanup_storage(storage_uri, document_id)
            existing = self.repository.idempotency(principal_hash, command.idempotency_key)
            if existing is None:
                raise exc
            if existing.request_fingerprint != fingerprint:
                raise IdempotencyMismatch() from exc
            replay = dict(existing.response_json)
            replay["idempotent_replay"] = True
            replay["trace_id"] = command.trace_id
            return replay
        except Exception:
            self.session.rollback()
            self._cleanup_storage(storage_uri, document_id)
            raise

    def get_document(self, document_id: UUID, trace_id: str) -> dict[str, Any]:
        document = self.repository.document(document_id)
        if document is None:
            raise DocumentNotFound(details={"document_id": str(document_id)})
        version = next(
            (
                item
                for item in document.versions
                if item.document_version_id == document.current_version_id
            ),
            None,
        )
        run = self.repository.run_for_shipment(document.shipment_id)
        return {
            "document_id": str(document.document_id),
            "shipment_id": str(document.shipment_id),
            "customer_id": str(document.shipment.customer_id),
            "document_type": _TYPE_TO_WIRE[document.document_type],
            "status": _STATUS_TO_WIRE[document.status],
            "run_id": str(run.verification_run_id) if run else None,
            "created_at": _iso(document.created_at),
            "updated_at": _iso(document.updated_at),
            "content": {
                "media_type": version.media_type if version else None,
                "size_bytes": version.byte_size if version else None,
                "content_sha256": version.content_sha256 if version else None,
                "download_url": None,
            },
            "extraction": None,
            "links": {
                "validation": f"/v1/documents/{document.document_id}/validation",
                "decision": f"/v1/documents/{document.document_id}/decision",
                "shipment": f"/v1/shipments/{document.shipment_id}",
            },
            "trace_id": trace_id,
        }

    def get_shipment(self, shipment_id: UUID, trace_id: str) -> dict[str, Any]:
        shipment = self.repository.shipment(shipment_id)
        if shipment is None:
            raise ShipmentNotFound(details={"shipment_id": str(shipment_id)})
        documents: list[dict[str, Any]] = []
        for document in shipment.documents:
            run = self.repository.run_for_shipment(shipment.shipment_id)
            documents.append(
                {
                    "document_id": str(document.document_id),
                    "document_type": _TYPE_TO_WIRE[document.document_type],
                    "status": _STATUS_TO_WIRE[document.status],
                    "run_id": str(run.verification_run_id) if run else None,
                }
            )
        return {
            "shipment_id": str(shipment.shipment_id),
            "customer_id": str(shipment.customer_id),
            "status": shipment.status.upper(),
            "document_ids": [item["document_id"] for item in documents],
            "documents": documents,
            "latest_decision": None,
            "created_at": _iso(shipment.created_at),
            "updated_at": _iso(shipment.updated_at),
            "trace_id": trace_id,
        }

    def _resolve_shipment(self, command: IngestCommand) -> Shipment:
        if command.shipment_id is not None:
            shipment = self.repository.shipment(command.shipment_id)
            if shipment is None or shipment.customer_id != command.customer_id:
                raise ShipmentNotFound(details={"shipment_id": str(command.shipment_id)})
            return shipment
        shipment = Shipment(customer_id=command.customer_id, status="open")
        self.repository.add(shipment)
        self.repository.flush()
        return shipment

    def _record_idempotency(
        self,
        command: IngestCommand,
        principal_hash: str,
        fingerprint: str,
        response: dict[str, Any],
        document_id: UUID,
        shipment_id: UUID,
        run_id: UUID,
    ) -> None:
        self.repository.add(
            IdempotencyRecord(
                principal_hash=principal_hash,
                idempotency_key=command.idempotency_key,
                request_fingerprint=fingerprint,
                document_id=document_id,
                shipment_id=shipment_id,
                verification_run_id=run_id,
                response_json=response,
            )
        )

    def _cleanup_storage(self, storage_uri: str | None, document_id: UUID) -> None:
        if storage_uri is None:
            return
        try:
            self.storage.delete(storage_uri)
        except Exception:
            logger.warning(
                "orphan_cleanup_failed",
                extra={"event": "storage.cleanup", "document_id": str(document_id)},
            )

    @staticmethod
    def _raise_processing_failure(error_code: str | None) -> Never:
        if error_code == DOC_PAYLOAD_TOO_LARGE:
            raise PayloadTooLarge()
        if error_code in {
            DOC_UNSUPPORTED_MEDIA_TYPE,
            DOC_UNSUPPORTED_EXTENSION,
            DOC_MIME_MISMATCH,
        }:
            raise UnsupportedMediaType()
        if error_code in {DOC_INVALID_FILENAME, DOC_PATH_TRAVERSAL}:
            raise UnsafeFilename()
        if error_code in {
            DOC_EMPTY,
            DOC_CORRUPT,
            DOC_UNREADABLE,
            DOC_TOO_MANY_PAGES,
        }:
            raise DocumentUnreadable()
        if error_code == DOC_INTERNAL:
            raise NovaError()
        raise NovaError()

    @staticmethod
    def _fingerprint(command: IngestCommand, content_sha: str) -> str:
        payload = {
            "method": "POST",
            "path": "/v1/documents",
            "customer_id": str(command.customer_id),
            "shipment_id": str(command.shipment_id) if command.shipment_id else None,
            "document_type": command.document_type,
            "external_ref": command.external_ref,
            "content_sha256": content_sha,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _accepted_response(
        document_id: UUID,
        shipment_id: UUID,
        run_id: UUID,
        trace_id: str,
        *,
        replay: bool,
    ) -> dict[str, Any]:
        return {
            "document_id": str(document_id),
            "shipment_id": str(shipment_id),
            "run_id": str(run_id),
            "status": "ACCEPTED",
            "idempotent_replay": replay,
            "trace_id": trace_id,
        }


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _as_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except ValueError:
        return None
