"""Read-time projection of document agreement from persisted extraction + validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from nova.domain.agreement import (
    AgreementCategory,
    DocumentAgreement,
    FieldConfidenceInput,
    ValidationCheckInput,
    agreement_wire,
    classify_document_agreement,
)
from nova.extraction.fields import required_fields_for
from nova.persistence.models import (
    DecisionRecord,
    Document,
    ExtractedFieldRow,
    Shipment,
    ValidationRecordRow,
    VerificationRun,
)


def _checks_from_validation(validation: ValidationRecordRow | None) -> list[ValidationCheckInput]:
    if validation is None:
        return []
    payload = validation.result_json or {}
    raw_checks = payload.get("checks") or []
    checks: list[ValidationCheckInput] = []
    for item in raw_checks:
        if not isinstance(item, dict):
            continue
        outcome = str(item.get("outcome") or item.get("result") or "")
        checks.append(
            ValidationCheckInput(
                field_name=item.get("field_name"),
                outcome=outcome,
            )
        )
    return checks


def _fields_from_rows(rows: list[ExtractedFieldRow]) -> list[FieldConfidenceInput]:
    return [
        FieldConfidenceInput(
            field_name=row.field_key,
            confidence=row.confidence,
            presence=row.presence,
            is_missing=bool(row.is_missing),
        )
        for row in rows
    ]


def classify_from_persisted(
    *,
    document_type: str,
    extracted_rows: list[ExtractedFieldRow],
    validation: ValidationRecordRow | None,
) -> DocumentAgreement:
    return classify_document_agreement(
        required_fields=required_fields_for(document_type),
        fields=_fields_from_rows(extracted_rows),
        validation_status=validation.status if validation is not None else None,
        checks=_checks_from_validation(validation),
    )


def latest_run_for_document(session: Session, document: Document) -> VerificationRun | None:
    return session.scalar(
        select(VerificationRun)
        .where(VerificationRun.shipment_id == document.shipment_id)
        .order_by(VerificationRun.created_at.desc())
        .limit(1)
    )


def latest_validation_for_document(
    session: Session,
    document_id: UUID,
) -> ValidationRecordRow | None:
    return session.scalar(
        select(ValidationRecordRow)
        .where(ValidationRecordRow.document_id == document_id)
        .order_by(ValidationRecordRow.created_at.desc())
        .limit(1)
    )


def extracted_rows_for_run(session: Session, run_id: UUID) -> list[ExtractedFieldRow]:
    return list(
        session.scalars(
            select(ExtractedFieldRow).where(ExtractedFieldRow.verification_run_id == run_id)
        )
    )


def agreement_for_document(session: Session, document: Document) -> DocumentAgreement:
    run = latest_run_for_document(session, document)
    validation = latest_validation_for_document(session, document.document_id)
    rows = extracted_rows_for_run(session, run.verification_run_id) if run else []
    return classify_from_persisted(
        document_type=document.document_type,
        extracted_rows=rows,
        validation=validation,
    )


def invoice_number_from_rows(rows: list[ExtractedFieldRow]) -> str | None:
    for row in rows:
        if row.field_key == "invoice_number" and row.value_json is not None:
            return str(row.value_json)
    return None


def enrich_document_item(
    session: Session,
    document: Document,
    *,
    customer_id: UUID,
    type_wire: dict[str, str],
    status_wire: dict[str, str],
    iso: Any,
) -> dict[str, Any]:
    """Build a list/detail document projection including agreement fields."""
    run = latest_run_for_document(session, document)
    validation = latest_validation_for_document(session, document.document_id)
    rows = extracted_rows_for_run(session, run.verification_run_id) if run else []
    agreement = classify_from_persisted(
        document_type=document.document_type,
        extracted_rows=rows,
        validation=validation,
    )
    decision = session.scalar(
        select(DecisionRecord)
        .where(DecisionRecord.document_id == document.document_id)
        .order_by(DecisionRecord.decided_at.desc())
        .limit(1)
    )
    item: dict[str, Any] = {
        "document_id": str(document.document_id),
        "shipment_id": str(document.shipment_id),
        "customer_id": str(customer_id),
        "document_type": type_wire.get(document.document_type, "OTHER"),
        "status": status_wire.get(document.status, document.status.upper()),
        "run_id": str(run.verification_run_id) if run else None,
        "created_at": iso(document.created_at),
        "updated_at": iso(document.updated_at),
        **agreement_wire(agreement),
        "decision": decision.disposition if decision else None,
        "validation_result": validation.aggregate_result if validation else None,
        "invoice_number": invoice_number_from_rows(rows),
    }
    return item


def iter_customer_documents(
    session: Session,
    customer_id: UUID,
    *,
    updated_after: datetime | None = None,
    updated_before: datetime | None = None,
) -> list[Document]:
    filters = [
        Shipment.customer_id == customer_id,
        Document.deleted_at.is_(None),
        Shipment.deleted_at.is_(None),
    ]
    if updated_after is not None:
        filters.append(Document.updated_at >= updated_after)
    if updated_before is not None:
        filters.append(Document.updated_at < updated_before)
    return list(
        session.scalars(
            select(Document)
            .join(Shipment, Shipment.shipment_id == Document.shipment_id)
            .where(*filters)
            .order_by(Document.updated_at.desc())
        )
    )


def agreement_counts_for_customer(
    session: Session,
    customer_id: UUID,
    *,
    updated_after: datetime | None = None,
    updated_before: datetime | None = None,
) -> dict[str, int]:
    counts = {
        AgreementCategory.STRONG_AGREEMENT.value: 0,
        AgreementCategory.PARTIAL_AGREEMENT.value: 0,
        AgreementCategory.WEAK_AGREEMENT.value: 0,
    }
    for document in iter_customer_documents(
        session,
        customer_id,
        updated_after=updated_after,
        updated_before=updated_before,
    ):
        category = agreement_for_document(session, document).category.value
        counts[category] = counts.get(category, 0) + 1
    return counts


def documents_matching_agreement(
    session: Session,
    customer_id: UUID,
    agreement: AgreementCategory | str,
    *,
    limit: int,
    updated_after: datetime | None = None,
    updated_before: datetime | None = None,
) -> list[tuple[Document, DocumentAgreement, DecisionRecord | None, str | None]]:
    target = AgreementCategory(str(agreement))
    matched: list[tuple[Document, DocumentAgreement, DecisionRecord | None, str | None]] = []
    for document in iter_customer_documents(
        session,
        customer_id,
        updated_after=updated_after,
        updated_before=updated_before,
    ):
        run = latest_run_for_document(session, document)
        validation = latest_validation_for_document(session, document.document_id)
        rows = extracted_rows_for_run(session, run.verification_run_id) if run else []
        result = classify_from_persisted(
            document_type=document.document_type,
            extracted_rows=rows,
            validation=validation,
        )
        if result.category != target:
            continue
        decision = session.scalar(
            select(DecisionRecord)
            .where(DecisionRecord.document_id == document.document_id)
            .order_by(DecisionRecord.decided_at.desc())
            .limit(1)
        )
        matched.append((document, result, decision, invoice_number_from_rows(rows)))
        if len(matched) >= limit:
            break
    return matched
