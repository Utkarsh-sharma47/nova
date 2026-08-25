"""Parameterized read repository for Part 1 query intents (no dynamic SQL)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from nova.application.agreement_projection import (
    agreement_counts_for_customer,
    documents_matching_agreement,
)
from nova.domain.agreement import AgreementCategory, DocumentAgreement
from nova.persistence.models import (
    DecisionRecord,
    Document,
    ExtractedFieldRow,
    Shipment,
    ValidationRecordRow,
    VerificationRun,
)

_STATUS_TO_WIRE = {
    "registered": "ACCEPTED",
    "content_available": "ACCEPTED",
    "in_pipeline": "PROCESSING",
    "extracted": "EXTRACTED",
    "validated": "VALIDATED",
    "decided": "DECIDED",
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
    ) -> ValidationRecordRow | None:
        document = self.document_for_customer(customer_id, document_id)
        if document is None:
            return None
        return self.session.scalar(
            select(ValidationRecordRow)
            .where(ValidationRecordRow.document_id == document_id)
            .order_by(ValidationRecordRow.created_at.desc())
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
        decided_after: datetime | None = None,
        decided_before: datetime | None = None,
    ) -> list[tuple[Shipment, DecisionRecord]]:
        filters = [
            Shipment.customer_id == customer_id,
            Shipment.deleted_at.is_(None),
            DecisionRecord.disposition == disposition,
        ]
        if decided_after is not None:
            filters.append(DecisionRecord.decided_at >= decided_after)
        if decided_before is not None:
            filters.append(DecisionRecord.decided_at < decided_before)
        rows = self.session.execute(
            select(Shipment, DecisionRecord)
            .join(DecisionRecord, DecisionRecord.shipment_id == Shipment.shipment_id)
            .options(selectinload(Shipment.documents))
            .where(*filters)
            .order_by(DecisionRecord.decided_at.desc())
            .limit(limit)
        ).all()
        return [(shipment, decision) for shipment, decision in rows]

    def count_documents_by_agreement(
        self,
        customer_id: UUID,
        agreement: str,
        *,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
    ) -> int:
        counts = agreement_counts_for_customer(
            self.session,
            customer_id,
            updated_after=updated_after,
            updated_before=updated_before,
        )
        return int(counts.get(str(agreement).upper(), 0))

    def documents_by_agreement(
        self,
        customer_id: UUID,
        agreement: str,
        *,
        limit: int,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
    ) -> list[tuple[Document, DocumentAgreement, DecisionRecord | None, str | None]]:
        return documents_matching_agreement(
            self.session,
            customer_id,
            AgreementCategory(str(agreement).upper()),
            limit=limit,
            updated_after=updated_after,
            updated_before=updated_before,
        )

    def count_documents_requiring_attention(
        self,
        customer_id: UUID,
        *,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
    ) -> int:
        counts = agreement_counts_for_customer(
            self.session,
            customer_id,
            updated_after=updated_after,
            updated_before=updated_before,
        )
        return int(counts.get(AgreementCategory.PARTIAL_AGREEMENT.value, 0)) + int(
            counts.get(AgreementCategory.WEAK_AGREEMENT.value, 0)
        )

    def count_documents_by_decision(
        self,
        customer_id: UUID,
        disposition: str,
        *,
        decided_after: datetime | None = None,
        decided_before: datetime | None = None,
    ) -> int:
        filters = [
            Shipment.customer_id == customer_id,
            Shipment.deleted_at.is_(None),
            Document.deleted_at.is_(None),
            DecisionRecord.disposition == disposition,
        ]
        if decided_after is not None:
            filters.append(DecisionRecord.decided_at >= decided_after)
        if decided_before is not None:
            filters.append(DecisionRecord.decided_at < decided_before)
        # Count distinct documents with the disposition (latest decision per doc via join).
        result = self.session.scalar(
            select(func.count(func.distinct(DecisionRecord.document_id)))
            .join(Document, Document.document_id == DecisionRecord.document_id)
            .join(Shipment, Shipment.shipment_id == Document.shipment_id)
            .where(*filters)
        )
        return int(result or 0)

    def count_documents_with_mismatches(
        self,
        customer_id: UUID,
        *,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
    ) -> int:
        filters = [
            Shipment.customer_id == customer_id,
            Shipment.deleted_at.is_(None),
            Document.deleted_at.is_(None),
            ValidationRecordRow.aggregate_result == "MISMATCH",
        ]
        if updated_after is not None:
            filters.append(Document.updated_at >= updated_after)
        if updated_before is not None:
            filters.append(Document.updated_at < updated_before)
        result = self.session.scalar(
            select(func.count(func.distinct(ValidationRecordRow.document_id)))
            .join(Document, Document.document_id == ValidationRecordRow.document_id)
            .join(Shipment, Shipment.shipment_id == Document.shipment_id)
            .where(*filters)
        )
        return int(result or 0)

    def extracted_fields_for_run(self, run_id: UUID) -> list[ExtractedFieldRow]:
        return list(
            self.session.scalars(
                select(ExtractedFieldRow).where(ExtractedFieldRow.verification_run_id == run_id)
            )
        )

    def validation_for_run(self, run_id: UUID) -> ValidationRecordRow | None:
        return self.session.scalar(
            select(ValidationRecordRow).where(ValidationRecordRow.verification_run_id == run_id)
        )

    def decision_for_run(self, run_id: UUID) -> DecisionRecord | None:
        return self.session.scalar(
            select(DecisionRecord).where(DecisionRecord.verification_run_id == run_id)
        )

    def failing_checks(self, validation: ValidationRecordRow) -> list[dict[str, Any]]:
        """Derive failing checks from ValidationResult JSON (Phase 7 persistence)."""
        payload = validation.result_json or {}
        checks = payload.get("checks") or []
        failing: list[dict[str, Any]] = []
        for check in checks:
            if not isinstance(check, dict):
                continue
            outcome = str(check.get("outcome") or check.get("result") or "")
            if outcome not in {"MISMATCH", "UNCERTAIN"}:
                continue
            failing.append(
                {
                    "check_id": str(check.get("check_id") or ""),
                    "rule_key": str(check.get("rule_code") or check.get("rule_id") or ""),
                    "field": check.get("field_name"),
                    "result": outcome,
                    "reason_code": check.get("error_code") or outcome,
                    "reason_detail": check.get("reason"),
                }
            )
        return failing

    @staticmethod
    def document_status_wire(status: str) -> str:
        return _STATUS_TO_WIRE.get(status, status.upper())

    @staticmethod
    def document_type_wire(document_type: str) -> str:
        return _TYPE_TO_WIRE.get(document_type, "OTHER")
