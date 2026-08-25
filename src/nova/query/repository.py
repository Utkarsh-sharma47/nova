"""Parameterized read repository for Part 1 query intents (no dynamic SQL)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from nova.persistence.models import (
    DecisionRecord,
    Document,
    ExtractedFieldRow,
    Shipment,
    ValidationCheckRow,
    ValidationRow,
    VerificationRun,
)

_STATUS_TO_WIRE = {
    "registered": "ACCEPTED",
    "content_available": "ACCEPTED",
    "in_pipeline": "PROCESSING",
    "extracted": "EXTRACTED",
    "failed": "FAILED",
    "superseded": "FAILED",
    "withdrawn": "FAILED",
}
_TYPE_TO_WIRE = {
    "commercial_invoice": "INVOICE",
    "bill_of_lading": "BILL_OF_LADING",
    "packing_list": "OTHER",
    "other": "OTHER",
}


class QueryRepository:
    """Customer-scoped, allow-listed reads against the system of record."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def shipment_for_customer(
        self,
        customer_id: UUID,
        shipment_id: UUID,
    ) -> Shipment | None:
        return self.session.scalar(
            select(Shipment)
            .options(selectinload(Shipment.documents))
            .where(
                Shipment.shipment_id == shipment_id,
                Shipment.customer_id == customer_id,
                Shipment.deleted_at.is_(None),
            )
        )

    def document_for_customer(
        self,
        customer_id: UUID,
        document_id: UUID,
    ) -> Document | None:
        return self.session.scalar(
            select(Document)
            .join(Shipment, Shipment.shipment_id == Document.shipment_id)
            .options(selectinload(Document.shipment), selectinload(Document.versions))
            .where(
                Document.document_id == document_id,
                Shipment.customer_id == customer_id,
                Document.deleted_at.is_(None),
                Shipment.deleted_at.is_(None),
            )
        )

    def documents_for_shipment(
        self,
        customer_id: UUID,
        shipment_id: UUID,
    ) -> list[Document]:
        shipment = self.shipment_for_customer(customer_id, shipment_id)
        if shipment is None:
            return []
        return list(shipment.documents)

    def latest_run_for_shipment(self, shipment_id: UUID) -> VerificationRun | None:
        return self.session.scalar(
            select(VerificationRun)
            .where(VerificationRun.shipment_id == shipment_id)
            .order_by(VerificationRun.created_at.desc())
            .limit(1)
        )

    def run_for_customer(
        self,
        customer_id: UUID,
        run_id: UUID,
    ) -> VerificationRun | None:
        return self.session.scalar(
            select(VerificationRun)
            .join(Shipment, Shipment.shipment_id == VerificationRun.shipment_id)
            .where(
                VerificationRun.verification_run_id == run_id,
                Shipment.customer_id == customer_id,
                Shipment.deleted_at.is_(None),
            )
        )

    def validation_for_document(
        self,
        customer_id: UUID,
        document_id: UUID,
    ) -> ValidationRow | None:
        document = self.document_for_customer(customer_id, document_id)
        if document is None:
            return None
        return self.session.scalar(
            select(ValidationRow)
            .options(selectinload(ValidationRow.checks))
            .where(ValidationRow.document_id == document_id)
            .order_by(ValidationRow.created_at.desc())
            .limit(1)
        )

    def decision_for_document(
        self,
        customer_id: UUID,
        document_id: UUID,
    ) -> DecisionRecord | None:
        document = self.document_for_customer(customer_id, document_id)
        if document is None:
            return None
        return self.session.scalar(
            select(DecisionRecord)
            .where(DecisionRecord.document_id == document_id)
            .order_by(DecisionRecord.decided_at.desc())
            .limit(1)
        )

    def shipments_by_decision(
        self,
        customer_id: UUID,
        disposition: str,
        *,
        limit: int,
    ) -> list[tuple[Shipment, DecisionRecord]]:
        rows = self.session.execute(
            select(Shipment, DecisionRecord)
            .join(DecisionRecord, DecisionRecord.shipment_id == Shipment.shipment_id)
            .where(
                Shipment.customer_id == customer_id,
                Shipment.deleted_at.is_(None),
                DecisionRecord.disposition == disposition,
            )
            .order_by(DecisionRecord.decided_at.desc())
            .limit(limit)
        ).all()
        return [(shipment, decision) for shipment, decision in rows]

    def extracted_fields_for_run(self, run_id: UUID) -> list[ExtractedFieldRow]:
        return list(
            self.session.scalars(
                select(ExtractedFieldRow).where(ExtractedFieldRow.verification_run_id == run_id)
            )
        )

    def validation_for_run(self, run_id: UUID) -> ValidationRow | None:
        return self.session.scalar(
            select(ValidationRow)
            .options(selectinload(ValidationRow.checks))
            .where(ValidationRow.verification_run_id == run_id)
        )

    def decision_for_run(self, run_id: UUID) -> DecisionRecord | None:
        return self.session.scalar(
            select(DecisionRecord).where(DecisionRecord.verification_run_id == run_id)
        )

    def failing_checks(self, validation_id: UUID) -> list[ValidationCheckRow]:
        return list(
            self.session.scalars(
                select(ValidationCheckRow).where(
                    ValidationCheckRow.validation_id == validation_id,
                    ValidationCheckRow.result.in_(("MISMATCH", "UNCERTAIN")),
                )
            )
        )

    @staticmethod
    def document_status_wire(status: str) -> str:
        return _STATUS_TO_WIRE.get(status, status.upper())

    @staticmethod
    def document_type_wire(document_type: str) -> str:
        return _TYPE_TO_WIRE.get(document_type, "OTHER")
