"""SQLAlchemy repositories used by application services."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from nova.persistence.models import (
    AgentExecution,
    Customer,
    Document,
    IdempotencyRecord,
    Shipment,
    VerificationRun,
)


class NovaRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def customer(self, customer_id: UUID) -> Customer | None:
        return self.session.get(Customer, customer_id)

    def shipment(self, shipment_id: UUID) -> Shipment | None:
        return self.session.scalar(
            select(Shipment)
            .options(selectinload(Shipment.documents))
            .where(Shipment.shipment_id == shipment_id, Shipment.deleted_at.is_(None))
        )

    def document(self, document_id: UUID) -> Document | None:
        return self.session.scalar(
            select(Document)
            .options(selectinload(Document.versions), selectinload(Document.shipment))
            .where(Document.document_id == document_id, Document.deleted_at.is_(None))
        )

    def run_for_shipment(self, shipment_id: UUID) -> VerificationRun | None:
        return self.session.scalar(
            select(VerificationRun)
            .where(VerificationRun.shipment_id == shipment_id)
            .order_by(VerificationRun.created_at.desc())
            .limit(1)
        )

    def idempotency(self, principal_hash: str, key: str) -> IdempotencyRecord | None:
        return self.session.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.principal_hash == principal_hash,
                IdempotencyRecord.idempotency_key == key,
            )
        )

    def document_by_external_ref(
        self,
        customer_id: UUID,
        external_ref: str,
    ) -> Document | None:
        return self.session.scalar(
            select(Document)
            .join(Shipment, Shipment.shipment_id == Document.shipment_id)
            .options(selectinload(Document.versions))
            .where(
                Shipment.customer_id == customer_id,
                Document.external_ref == external_ref,
                Document.deleted_at.is_(None),
            )
        )

    def extractor_execution(self, verification_run_id: UUID) -> AgentExecution | None:
        return self.session.scalar(
            select(AgentExecution).where(
                AgentExecution.verification_run_id == verification_run_id,
                AgentExecution.stage == "extractor",
            )
        )

    def add(self, entity: object) -> None:
        self.session.add(entity)

    def flush(self) -> None:
        self.session.flush()
