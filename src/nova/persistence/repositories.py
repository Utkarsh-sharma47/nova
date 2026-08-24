"""Async repository helpers for Phase 3 ingestion entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nova.persistence.models import (
    CustomerModel,
    DocumentModel,
    DocumentVersionModel,
    IdempotencyRecordModel,
    ShipmentModel,
    VerificationRunModel,
)


class CustomerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, customer_id: UUID) -> CustomerModel | None:
        return await self._session.get(CustomerModel, customer_id)

    async def create(
        self,
        *,
        customer_id: UUID | None = None,
        name: str,
        external_key: str | None = None,
        status: str = "active",
        metadata: dict[str, Any] | None = None,
    ) -> CustomerModel:
        row = CustomerModel(
            name=name,
            external_key=external_key,
            status=status,
            metadata_json=metadata or {},
        )
        if customer_id is not None:
            row.customer_id = customer_id
        self._session.add(row)
        await self._session.flush()
        return row


class ShipmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, shipment_id: UUID) -> ShipmentModel | None:
        return await self._session.get(ShipmentModel, shipment_id)

    async def create(
        self,
        *,
        customer_id: UUID,
        shipment_id: UUID | None = None,
        customer_shipment_ref: str | None = None,
        status: str = "open",
        metadata: dict[str, Any] | None = None,
    ) -> ShipmentModel:
        row = ShipmentModel(
            customer_id=customer_id,
            customer_shipment_ref=customer_shipment_ref,
            status=status,
            metadata_json=metadata or {},
        )
        if shipment_id is not None:
            row.shipment_id = shipment_id
        self._session.add(row)
        await self._session.flush()
        return row


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, document_id: UUID) -> DocumentModel | None:
        return await self._session.get(DocumentModel, document_id)

    async def find_by_customer_external_ref(
        self, *, customer_id: UUID, external_ref: str
    ) -> DocumentModel | None:
        stmt = (
            select(DocumentModel)
            .join(ShipmentModel, DocumentModel.shipment_id == ShipmentModel.shipment_id)
            .where(
                ShipmentModel.customer_id == customer_id,
                DocumentModel.external_ref == external_ref,
                DocumentModel.deleted_at.is_(None),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        shipment_id: UUID,
        document_type: str,
        status: str = "received",
        display_name: str | None = None,
        ingestion_channel: str = "upload",
        external_ref: str | None = None,
        document_id: UUID | None = None,
    ) -> DocumentModel:
        row = DocumentModel(
            shipment_id=shipment_id,
            document_type=document_type,
            status=status,
            display_name=display_name,
            ingestion_channel=ingestion_channel,
            external_ref=external_ref,
        )
        if document_id is not None:
            row.document_id = document_id
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_status(self, document: DocumentModel, status: str) -> DocumentModel:
        document.status = status
        await self._session.flush()
        return document

    async def set_current_version(
        self, document: DocumentModel, version_id: UUID
    ) -> DocumentModel:
        document.current_version_id = version_id
        await self._session.flush()
        return document


class DocumentVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, document_version_id: UUID) -> DocumentVersionModel | None:
        return await self._session.get(DocumentVersionModel, document_version_id)

    async def find_by_shipment_type_hash(
        self, *, shipment_id: UUID, document_type: str, content_sha256: str
    ) -> DocumentVersionModel | None:
        stmt = select(DocumentVersionModel).where(
            DocumentVersionModel.shipment_id == shipment_id,
            DocumentVersionModel.document_type == document_type,
            DocumentVersionModel.content_sha256 == content_sha256,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        document_id: UUID,
        shipment_id: UUID,
        document_type: str,
        version_number: int,
        storage_uri: str,
        content_sha256: str,
        media_type: str,
        byte_size: int,
        original_filename: str | None = None,
        ingestion_idempotency_key: str | None = None,
        created_by: str | None = None,
        document_version_id: UUID | None = None,
    ) -> DocumentVersionModel:
        row = DocumentVersionModel(
            document_id=document_id,
            shipment_id=shipment_id,
            document_type=document_type,
            version_number=version_number,
            storage_uri=storage_uri,
            content_sha256=content_sha256,
            media_type=media_type,
            byte_size=byte_size,
            original_filename=original_filename,
            ingestion_idempotency_key=ingestion_idempotency_key,
            created_by=created_by,
        )
        if document_version_id is not None:
            row.document_version_id = document_version_id
        self._session.add(row)
        await self._session.flush()
        return row


class VerificationRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, verification_run_id: UUID) -> VerificationRunModel | None:
        return await self._session.get(VerificationRunModel, verification_run_id)

    async def get_latest_for_shipment(
        self, shipment_id: UUID
    ) -> VerificationRunModel | None:
        stmt = (
            select(VerificationRunModel)
            .where(VerificationRunModel.shipment_id == shipment_id)
            .order_by(VerificationRunModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        shipment_id: UUID,
        document_version_ids: list[UUID],
        status: str = "queued",
        idempotency_key: str | None = None,
        trigger: str = "upload",
        verification_run_id: UUID | None = None,
    ) -> VerificationRunModel:
        row = VerificationRunModel(
            shipment_id=shipment_id,
            status=status,
            idempotency_key=idempotency_key,
            trigger=trigger,
            document_version_ids=[str(v) for v in document_version_ids],
        )
        if verification_run_id is not None:
            row.verification_run_id = verification_run_id
        self._session.add(row)
        await self._session.flush()
        return row


class IdempotencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self, *, principal_hash: str, idempotency_key: str
    ) -> IdempotencyRecordModel | None:
        stmt = select(IdempotencyRecordModel).where(
            IdempotencyRecordModel.principal_hash == principal_hash,
            IdempotencyRecordModel.idempotency_key == idempotency_key,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        principal_hash: str,
        idempotency_key: str,
        request_fingerprint: str,
        document_id: UUID,
        shipment_id: UUID,
        verification_run_id: UUID,
        response_json: dict[str, Any],
        created_at: datetime | None = None,
    ) -> IdempotencyRecordModel:
        row = IdempotencyRecordModel(
            principal_hash=principal_hash,
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
            document_id=document_id,
            shipment_id=shipment_id,
            verification_run_id=verification_run_id,
            response_json=response_json,
        )
        if created_at is not None:
            row.created_at = created_at
        self._session.add(row)
        await self._session.flush()
        return row
