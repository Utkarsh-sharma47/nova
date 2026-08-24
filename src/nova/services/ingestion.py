"""Synchronous document ingestion (no LLM / agent calls)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from nova.config import Settings
from nova.domain.errors import (
    BadRequestError,
    CustomerNotFoundError,
    ExternalRefConflictError,
    IdempotencyKeyReuseMismatchError,
    MissingIdempotencyKeyError,
    PayloadTooLargeError,
    ShipmentNotFoundError,
    UnsupportedDocumentTypeError,
    ValidationFailedError,
)
from nova.domain.lifecycle import (
    ApiDocumentStatus,
    DocumentStatus,
    DocumentType,
    IngestionChannel,
    VerificationRunStatus,
    parse_wire_document_type,
)
from nova.infrastructure.storage import DocumentStoragePort, safe_filename
from nova.observability.logging import get_logger, get_trace_id
from nova.persistence.repositories import (
    CustomerRepository,
    DocumentRepository,
    DocumentVersionRepository,
    IdempotencyRepository,
    ShipmentRepository,
    VerificationRunRepository,
)

logger = get_logger(__name__)

_IDEMPOTENCY_KEY_RE = re.compile(r"^[A-Za-z0-9._~-]{8,128}$")


def validate_idempotency_key(key: str | None) -> str:
    if key is None or not key.strip():
        raise MissingIdempotencyKeyError()
    value = key.strip()
    if not _IDEMPOTENCY_KEY_RE.fullmatch(value):
        raise BadRequestError(
            "Idempotency-Key must be 8–128 characters matching [A-Za-z0-9._~-]+.",
            code="INVALID_IDEMPOTENCY_KEY",
            details={"idempotency_key_length": len(value)},
        )
    return value


def build_request_fingerprint(
    *,
    customer_id: UUID,
    content_sha256: str,
    document_type: DocumentType | str,
    external_ref: str | None,
) -> str:
    """Canonical fingerprint: POST|/v1/documents|customer_id|sha256|doc_type|external_ref."""
    doc_type = (
        document_type.value if isinstance(document_type, DocumentType) else str(document_type)
    )
    ref = external_ref if external_ref is not None else ""
    return (
        f"POST|/v1/documents|{customer_id}|{content_sha256}|{doc_type}|{ref}"
    )


def principal_hash_for_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class IngestionResult:
    document_id: UUID
    shipment_id: UUID
    run_id: UUID
    status: ApiDocumentStatus
    idempotent_replay: bool
    trace_id: str
    content_sha256: str

    def to_response_dict(self) -> dict[str, Any]:
        return {
            "document_id": str(self.document_id),
            "shipment_id": str(self.shipment_id),
            "run_id": str(self.run_id),
            "status": self.status.value,
            "idempotent_replay": self.idempotent_replay,
            "trace_id": self.trace_id,
        }


class DocumentIngestionService:
    """Persist document bytes + metadata and queue a verification run (no agents)."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        storage: DocumentStoragePort,
        settings: Settings,
        principal_token: str,
    ) -> None:
        self._session = session
        self._storage = storage
        self._settings = settings
        self._principal_hash = principal_hash_for_token(principal_token)
        self._customers = CustomerRepository(session)
        self._shipments = ShipmentRepository(session)
        self._documents = DocumentRepository(session)
        self._versions = DocumentVersionRepository(session)
        self._runs = VerificationRunRepository(session)
        self._idempotency = IdempotencyRepository(session)

    async def ingest(
        self,
        *,
        idempotency_key: str | None,
        customer_id: UUID,
        file_bytes: bytes | None,
        filename: str | None,
        media_type: str | None,
        document_type_hint: str | None = None,
        shipment_id: UUID | None = None,
        external_ref: str | None = None,
        source_path: str | None = None,
    ) -> IngestionResult:
        key = validate_idempotency_key(idempotency_key)
        trace_id = get_trace_id() or str(uuid4())

        customer = await self._customers.get(customer_id)
        if customer is None or customer.deleted_at is not None:
            raise CustomerNotFoundError(details={"customer_id": str(customer_id)})

        data, resolved_media, channel, original_name = self._resolve_bytes(
            file_bytes=file_bytes,
            filename=filename,
            media_type=media_type,
            source_path=source_path,
        )
        if len(data) > self._settings.max_document_size_bytes:
            raise PayloadTooLargeError(
                details={
                    "max_bytes": self._settings.max_document_size_bytes,
                    "actual_bytes": len(data),
                }
            )
        if resolved_media.lower() not in self._settings.allowed_mime_types:
            raise UnsupportedDocumentTypeError(
                details={"media_type": resolved_media},
            )

        try:
            doc_type = parse_wire_document_type(document_type_hint)
        except ValueError as exc:
            raise UnsupportedDocumentTypeError(
                details={"document_type": document_type_hint}
            ) from exc

        content_sha256 = hashlib.sha256(data).hexdigest()
        fingerprint = build_request_fingerprint(
            customer_id=customer_id,
            content_sha256=content_sha256,
            document_type=doc_type,
            external_ref=external_ref,
        )

        existing = await self._idempotency.get(
            principal_hash=self._principal_hash, idempotency_key=key
        )
        if existing is not None:
            if existing.request_fingerprint != fingerprint:
                raise IdempotencyKeyReuseMismatchError(
                    details={
                        "idempotency_key": key,
                        "expected_fingerprint": existing.request_fingerprint,
                        "actual_fingerprint": fingerprint,
                    }
                )
            body = dict(existing.response_json)
            body["idempotent_replay"] = True
            if "trace_id" not in body:
                body["trace_id"] = trace_id
            logger.info(
                "idempotent_replay",
                extra={
                    "idempotency_key": key,
                    "idempotency_replay": True,
                    "document_id": str(existing.document_id),
                    "shipment_id": str(existing.shipment_id),
                    "run_id": str(existing.verification_run_id),
                    "content_sha256": content_sha256,
                },
            )
            return IngestionResult(
                document_id=existing.document_id,
                shipment_id=existing.shipment_id,
                run_id=existing.verification_run_id,
                status=ApiDocumentStatus(body.get("status", ApiDocumentStatus.ACCEPTED.value)),
                idempotent_replay=True,
                trace_id=str(body.get("trace_id", trace_id)),
                content_sha256=content_sha256,
            )

        if external_ref:
            conflict = await self._documents.find_by_customer_external_ref(
                customer_id=customer_id, external_ref=external_ref
            )
            if conflict is not None:
                version = None
                if conflict.current_version_id is not None:
                    version = await self._versions.get(conflict.current_version_id)
                if version is not None and version.content_sha256 == content_sha256:
                    # Domain-level dedupe: same external_ref + digest → replay prior accept.
                    run = await self._runs.get_latest_for_shipment(conflict.shipment_id)
                    if run is None:
                        raise ExternalRefConflictError(
                            details={
                                "external_ref": external_ref,
                                "document_id": str(conflict.document_id),
                            }
                        )
                    result = IngestionResult(
                        document_id=conflict.document_id,
                        shipment_id=conflict.shipment_id,
                        run_id=run.verification_run_id,
                        status=ApiDocumentStatus.ACCEPTED,
                        idempotent_replay=True,
                        trace_id=trace_id,
                        content_sha256=content_sha256,
                    )
                    response = result.to_response_dict()
                    await self._idempotency.create(
                        principal_hash=self._principal_hash,
                        idempotency_key=key,
                        request_fingerprint=fingerprint,
                        document_id=conflict.document_id,
                        shipment_id=conflict.shipment_id,
                        verification_run_id=run.verification_run_id,
                        response_json=response,
                    )
                    return result
                raise ExternalRefConflictError(
                    details={
                        "external_ref": external_ref,
                        "document_id": str(conflict.document_id),
                    }
                )

        if shipment_id is not None:
            shipment = await self._shipments.get(shipment_id)
            if shipment is None or shipment.deleted_at is not None:
                raise ShipmentNotFoundError(details={"shipment_id": str(shipment_id)})
            if shipment.customer_id != customer_id:
                raise ValidationFailedError(
                    "shipment_id does not belong to customer_id.",
                    details={
                        "shipment_id": str(shipment_id),
                        "customer_id": str(customer_id),
                    },
                )
        else:
            shipment = await self._shipments.create(customer_id=customer_id, status="open")

        document = await self._documents.create(
            shipment_id=shipment.shipment_id,
            document_type=doc_type.value,
            status=DocumentStatus.RECEIVED.value,
            display_name=original_name,
            ingestion_channel=channel.value,
            external_ref=external_ref,
        )

        filename_safe = safe_filename(original_name)
        relative = (
            f"{customer_id}/{document.document_id}/v1/{filename_safe}"
        )
        storage_uri = self._storage.store(
            relative_path=relative,
            data=data,
            max_bytes=self._settings.max_document_size_bytes,
        )

        version = await self._versions.create(
            document_id=document.document_id,
            shipment_id=shipment.shipment_id,
            document_type=doc_type.value,
            version_number=1,
            storage_uri=storage_uri,
            content_sha256=content_sha256,
            media_type=resolved_media,
            byte_size=len(data),
            original_filename=original_name,
            ingestion_idempotency_key=key,
            created_by=self._principal_hash[:16],
        )
        await self._documents.set_current_version(document, version.document_version_id)
        await self._documents.update_status(document, DocumentStatus.STORED.value)

        run = await self._runs.create(
            shipment_id=shipment.shipment_id,
            document_version_ids=[version.document_version_id],
            status=VerificationRunStatus.QUEUED.value,
            idempotency_key=f"ingest:{key}",
            trigger=channel.value,
        )

        result = IngestionResult(
            document_id=document.document_id,
            shipment_id=shipment.shipment_id,
            run_id=run.verification_run_id,
            status=ApiDocumentStatus.ACCEPTED,
            idempotent_replay=False,
            trace_id=trace_id,
            content_sha256=content_sha256,
        )
        response = result.to_response_dict()
        await self._idempotency.create(
            principal_hash=self._principal_hash,
            idempotency_key=key,
            request_fingerprint=fingerprint,
            document_id=document.document_id,
            shipment_id=shipment.shipment_id,
            verification_run_id=run.verification_run_id,
            response_json=response,
        )

        logger.info(
            "document_ingested",
            extra={
                "idempotency_key": key,
                "idempotency_replay": False,
                "document_id": str(document.document_id),
                "shipment_id": str(shipment.shipment_id),
                "run_id": str(run.verification_run_id),
                "customer_id": str(customer_id),
                "content_sha256": content_sha256,
                "status": result.status.value,
            },
        )
        return result

    def _resolve_bytes(
        self,
        *,
        file_bytes: bytes | None,
        filename: str | None,
        media_type: str | None,
        source_path: str | None,
    ) -> tuple[bytes, str, IngestionChannel, str | None]:
        has_file = file_bytes is not None
        has_path = source_path is not None and source_path.strip() != ""
        if has_file == has_path:
            raise BadRequestError(
                "Exactly one of file or source_path is required.",
                code="INVALID_INGESTION_INPUT",
            )
        if has_file:
            assert file_bytes is not None
            mime = (media_type or "application/octet-stream").split(";")[0].strip().lower()
            return file_bytes, mime, IngestionChannel.UPLOAD, filename

        assert source_path is not None
        # Only allow reading files that already live under the configured storage root
        # via a relative path (demo path-based intake).
        from pathlib import Path

        from nova.infrastructure.storage import LocalFilesystemDocumentStorage

        if not isinstance(self._storage, LocalFilesystemDocumentStorage):
            raise ValidationFailedError(
                "source_path ingestion requires local filesystem storage.",
                code="SOURCE_PATH_UNSUPPORTED",
            )
        rel = source_path.strip().lstrip("/")
        target = (self._storage.root / rel).resolve()
        try:
            target.relative_to(self._storage.root)
        except ValueError as exc:
            raise ValidationFailedError(
                "source_path escapes storage root.",
                code="INVALID_SOURCE_PATH",
            ) from exc
        if not target.is_file():
            raise ValidationFailedError(
                "source_path does not refer to an existing file.",
                code="INVALID_SOURCE_PATH",
                details={"source_path": source_path},
            )
        data = target.read_bytes()
        mime = (media_type or "application/octet-stream").split(";")[0].strip().lower()
        return data, mime, IngestionChannel.PATH, Path(target).name
