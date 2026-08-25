"""Operational read projections for the Part 1 UI (counts + recent rows)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nova.domain.errors import CustomerNotFound, ValidationFailure
from nova.persistence.models import (
    Customer,
    DecisionRecord,
    Document,
    Shipment,
    ValidationRecordRow,
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
_PROCESSING_STATUSES = {
    "registered",
    "content_available",
    "in_pipeline",
    "extracted",
    "validated",
}


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


class OpsService:
    """Customer-scoped aggregates for the operations dashboard."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_customer(self, customer_id: UUID) -> Customer:
        customer = self.session.get(Customer, customer_id)
        if customer is None or customer.deleted_at is not None:
            raise CustomerNotFound(details={"customer_id": str(customer_id)})
        return customer

    def create_customer(self, *, name: str, trace_id: str) -> dict[str, Any]:
        cleaned = name.strip()
        if not cleaned:
            raise ValidationFailure("Customer name is required.", details={"field": "name"})
        customer = Customer(name=cleaned, status="active")
        self.session.add(customer)
        self.session.commit()
        return {
            "customer_id": str(customer.customer_id),
            "name": customer.name,
            "status": customer.status,
            "created_at": _iso(customer.created_at),
            "trace_id": trace_id,
        }

    def list_documents(
        self,
        customer_id: UUID,
        *,
        limit: int,
        trace_id: str,
    ) -> dict[str, Any]:
        self.ensure_customer(customer_id)
        capped = max(1, min(limit, 100))
        rows = self.session.scalars(
            select(Document)
            .join(Shipment, Shipment.shipment_id == Document.shipment_id)
            .where(
                Shipment.customer_id == customer_id,
                Document.deleted_at.is_(None),
                Shipment.deleted_at.is_(None),
            )
            .order_by(Document.updated_at.desc())
            .limit(capped)
        ).all()
        items = [
            {
                "document_id": str(doc.document_id),
                "shipment_id": str(doc.shipment_id),
                "customer_id": str(customer_id),
                "document_type": _TYPE_TO_WIRE.get(doc.document_type, "OTHER"),
                "status": _STATUS_TO_WIRE.get(doc.status, doc.status.upper()),
                "run_id": None,
                "created_at": _iso(doc.created_at),
                "updated_at": _iso(doc.updated_at),
            }
            for doc in rows
        ]
        return {"items": items, "limit": capped, "trace_id": trace_id}

    def summary(self, customer_id: UUID, *, trace_id: str) -> dict[str, Any]:
        self.ensure_customer(customer_id)

        documents = self.session.scalars(
            select(Document)
            .join(Shipment, Shipment.shipment_id == Document.shipment_id)
            .where(
                Shipment.customer_id == customer_id,
                Document.deleted_at.is_(None),
                Shipment.deleted_at.is_(None),
            )
            .order_by(Document.updated_at.desc())
        ).all()

        processing = sum(1 for d in documents if d.status in _PROCESSING_STATUSES)
        decided = sum(1 for d in documents if d.status == "decided")
        failed = sum(1 for d in documents if d.status in {"failed", "superseded", "withdrawn"})

        decision_counts: dict[str, int] = {
            str(disposition): int(count)
            for disposition, count in self.session.execute(
                select(DecisionRecord.disposition, func.count())
                .join(Shipment, Shipment.shipment_id == DecisionRecord.shipment_id)
                .where(
                    Shipment.customer_id == customer_id,
                    Shipment.deleted_at.is_(None),
                )
                .group_by(DecisionRecord.disposition)
            ).all()
        }
        validation_counts: dict[str, int] = {
            str(result): int(count)
            for result, count in self.session.execute(
                select(ValidationRecordRow.aggregate_result, func.count())
                .join(Shipment, Shipment.shipment_id == ValidationRecordRow.shipment_id)
                .where(
                    Shipment.customer_id == customer_id,
                    Shipment.deleted_at.is_(None),
                    ValidationRecordRow.aggregate_result.is_not(None),
                )
                .group_by(ValidationRecordRow.aggregate_result)
            ).all()
            if result is not None
        }

        recent_decisions = self.session.scalars(
            select(DecisionRecord)
            .join(Shipment, Shipment.shipment_id == DecisionRecord.shipment_id)
            .where(
                Shipment.customer_id == customer_id,
                Shipment.deleted_at.is_(None),
            )
            .order_by(DecisionRecord.decided_at.desc())
            .limit(10)
        ).all()

        recent_documents = [
            {
                "document_id": str(doc.document_id),
                "shipment_id": str(doc.shipment_id),
                "customer_id": str(customer_id),
                "document_type": _TYPE_TO_WIRE.get(doc.document_type, "OTHER"),
                "status": _STATUS_TO_WIRE.get(doc.status, doc.status.upper()),
                "run_id": None,
                "created_at": _iso(doc.created_at),
                "updated_at": _iso(doc.updated_at),
            }
            for doc in documents[:10]
        ]

        return {
            "customer_id": str(customer_id),
            "totals": {
                "documents": len(documents),
                "processing": processing,
                "decided": decided,
                "failed": failed,
                "human_review": int(decision_counts.get("HUMAN_REVIEW", 0)),
                "amendment_request": int(decision_counts.get("AMENDMENT_REQUEST", 0)),
                "auto_approve": int(decision_counts.get("AUTO_APPROVE", 0)),
            },
            "validation_outcomes": {
                "MATCH": int(validation_counts.get("MATCH", 0)),
                "MISMATCH": int(validation_counts.get("MISMATCH", 0)),
                "UNCERTAIN": int(validation_counts.get("UNCERTAIN", 0)),
            },
            "recent_documents": recent_documents,
            "recent_decisions": [
                {
                    "decision_id": str(row.decision_id),
                    "document_id": str(row.document_id),
                    "shipment_id": str(row.shipment_id),
                    "decision": row.disposition,
                    "created_at": _iso(row.decided_at),
                }
                for row in recent_decisions
            ],
            "trace_id": trace_id,
        }
