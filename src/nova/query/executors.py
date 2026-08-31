"""Allow-listed intent executors grounded in QueryRepository results."""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from nova.contracts.query import (
    InterpretedIntent,
    QueryCitation,
    QueryIntentName,
    QueryResultPayload,
    QueryStatus,
)
from nova.query.repository import QueryRepository


class MissingEntityError(Exception):
    """Raised when a required entity is not visible for the customer."""

    def __init__(self, entity: str, entity_id: str) -> None:
        super().__init__(f"{entity} {entity_id} not found")
        self.entity = entity
        self.entity_id = entity_id


def _parse_uuid(parameters: dict[str, Any], key: str) -> UUID:
    raw = parameters.get(key)
    if raw is None:
        raise ValueError(f"missing parameter {key}")
    return UUID(str(raw))


class IntentHandler(Protocol):
    def __call__(
        self,
        parameters: dict[str, Any],
        *,
        customer_id: UUID,
        repository: QueryRepository,
        max_results: int,
    ) -> tuple[QueryStatus, QueryResultPayload]: ...


def intent_handlers() -> dict[QueryIntentName, IntentHandler]:
    """Allow-listed intent -> executor. Every intent must appear here."""
    return {
        QueryIntentName.GET_SHIPMENT: _get_shipment,
        QueryIntentName.GET_DOCUMENT: _get_document,
        QueryIntentName.GET_DOCUMENT_VALIDATION: _get_document_validation,
        QueryIntentName.GET_DOCUMENT_DECISION: _get_document_decision,
        QueryIntentName.LIST_SHIPMENTS_BY_DECISION: _list_shipments_by_decision,
        QueryIntentName.LIST_DOCUMENTS_FOR_SHIPMENT: _list_documents_for_shipment,
        QueryIntentName.SUMMARIZE_RUN: _summarize_run,
        QueryIntentName.COUNT_DOCUMENTS_BY_AGREEMENT: _count_documents_by_agreement,
        QueryIntentName.LIST_DOCUMENTS_BY_AGREEMENT: _list_documents_by_agreement,
        QueryIntentName.COUNT_DOCUMENTS_REQUIRING_ATTENTION: _count_documents_requiring_attention,
        QueryIntentName.COUNT_DOCUMENTS_BY_DECISION: _count_documents_by_decision,
        QueryIntentName.COUNT_DOCUMENTS_WITH_MISMATCHES: _count_documents_with_mismatches,
        QueryIntentName.COUNT_DOCUMENTS: _count_documents,
        QueryIntentName.COUNT_SHIPMENTS: _count_shipments,
        QueryIntentName.LIST_SHIPMENTS: _list_shipments,
        QueryIntentName.LIST_RECENT_DOCUMENTS: _list_recent_documents,
        QueryIntentName.LIST_DOCUMENTS_BY_DECISION: _list_documents_by_decision,
        QueryIntentName.LIST_DOCUMENTS_BY_CONFIDENCE: _list_documents_by_confidence,
        QueryIntentName.LIST_DOCUMENTS_WITH_MISMATCHES: _list_documents_with_mismatches,
        QueryIntentName.LIST_DOCUMENTS_WITH_UNCERTAIN_VALIDATION: (
            _list_documents_with_uncertain_validation
        ),
        QueryIntentName.GET_DOCUMENT_MISMATCHED_FIELDS: _get_document_mismatched_fields,
        QueryIntentName.EXPLAIN_DOCUMENT_REVIEW: _explain_document_review,
        QueryIntentName.COMPARE_AGREEMENT: _compare_agreement,
    }


def execute_intent(
    intent: InterpretedIntent,
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    handler = intent_handlers()[intent.name]
    return handler(
        intent.parameters,
        customer_id=customer_id,
        repository=repository,
        max_results=max_results,
    )


def _get_shipment(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    del max_results
    shipment_id = _parse_uuid(parameters, "shipment_id")
    shipment = repository.shipment_for_customer(customer_id, shipment_id)
    if shipment is None:
        raise MissingEntityError("shipment", str(shipment_id))
    document_ids = [str(doc.document_id) for doc in shipment.documents]
    run = repository.latest_run_for_shipment(shipment.shipment_id)
    decision = None
    if shipment.documents:
        decision = repository.decision_for_document(
            customer_id,
            shipment.documents[0].document_id,
        )
    record = {
        "type": "shipment",
        "shipment_id": str(shipment.shipment_id),
        "customer_id": str(shipment.customer_id),
        "status": shipment.status,
        "document_ids": document_ids,
        "run_id": str(run.verification_run_id) if run else None,
        "decision": decision.disposition if decision else None,
        "updated_at": shipment.updated_at.isoformat(),
    }
    citations = [
        QueryCitation(
            type="shipment",
            id=str(shipment.shipment_id),
            shipment_id=str(shipment.shipment_id),
            run_id=str(run.verification_run_id) if run else None,
        )
    ]
    if decision is not None:
        citations.append(
            QueryCitation(
                type="decision",
                id=str(decision.decision_id),
                decision_id=str(decision.decision_id),
                shipment_id=str(shipment.shipment_id),
                document_id=str(decision.document_id),
            )
        )
    summary = (
        f"Shipment {shipment.shipment_id} is {shipment.status} "
        f"with {len(document_ids)} document(s)."
    )
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary=summary,
        records=[record],
        citations=citations,
    )


def _get_document(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    del max_results
    document_id = _parse_uuid(parameters, "document_id")
    document = repository.document_for_customer(customer_id, document_id)
    if document is None:
        raise MissingEntityError("document", str(document_id))
    run = repository.latest_run_for_shipment(document.shipment_id)
    record = {
        "type": "document",
        "document_id": str(document.document_id),
        "shipment_id": str(document.shipment_id),
        "customer_id": str(document.shipment.customer_id),
        "document_type": repository.document_type_wire(document.document_type),
        "status": repository.document_status_wire(document.status),
        "run_id": str(run.verification_run_id) if run else None,
        "updated_at": document.updated_at.isoformat(),
    }
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary=(
            f"Document {document.document_id} status is "
            f"{repository.document_status_wire(document.status)}."
        ),
        records=[record],
        citations=[
            QueryCitation(
                type="document",
                id=str(document.document_id),
                document_id=str(document.document_id),
                shipment_id=str(document.shipment_id),
                run_id=str(run.verification_run_id) if run else None,
            )
        ],
    )


def _get_document_validation(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    del max_results
    document_id = _parse_uuid(parameters, "document_id")
    document = repository.document_for_customer(customer_id, document_id)
    if document is None:
        raise MissingEntityError("document", str(document_id))
    validation = repository.validation_for_document(customer_id, document_id)
    if validation is None:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"No validation record exists for document {document_id}.",
            records=[],
            citations=[
                QueryCitation(
                    type="document",
                    id=str(document_id),
                    document_id=str(document_id),
                    shipment_id=str(document.shipment_id),
                )
            ],
        )
    failing = repository.failing_checks(validation)
    record = {
        "type": "validation",
        "validation_id": str(validation.validation_id),
        "document_id": str(document_id),
        "shipment_id": str(validation.shipment_id),
        "run_id": str(validation.verification_run_id),
        "status": validation.status,
        "overall_result": validation.aggregate_result,
        "failure_count": len(failing),
        "failures": failing,
        "completed_at": validation.completed_at.isoformat() if validation.completed_at else None,
    }
    citations = [
        QueryCitation(
            type="validation",
            id=str(validation.validation_id),
            validation_id=str(validation.validation_id),
            document_id=str(document_id),
            shipment_id=str(validation.shipment_id),
            run_id=str(validation.verification_run_id),
            code=validation.aggregate_result,
        )
    ]
    for item in failing:
        citations.append(
            QueryCitation(
                type="validation_check",
                id=item["check_id"],
                validation_id=str(validation.validation_id),
                document_id=str(document_id),
                field=item["field"],
                code=item["reason_code"],
            )
        )
    summary = (
        f"Validation for document {document_id} is {validation.aggregate_result} "
        f"with {len(failing)} failing check(s)."
    )
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary=summary,
        records=[record],
        citations=citations,
    )


def _get_document_decision(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    del max_results
    document_id = _parse_uuid(parameters, "document_id")
    document = repository.document_for_customer(customer_id, document_id)
    if document is None:
        raise MissingEntityError("document", str(document_id))
    decision = repository.decision_for_document(customer_id, document_id)
    if decision is None:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"No decision record exists for document {document_id}.",
            records=[],
            citations=[
                QueryCitation(
                    type="document",
                    id=str(document_id),
                    document_id=str(document_id),
                    shipment_id=str(document.shipment_id),
                )
            ],
        )
    reasons = list(decision.reasons or [])
    reason_codes = list(decision.reason_codes or [])
    record = {
        "type": "decision",
        "decision_id": str(decision.decision_id),
        "document_id": str(decision.document_id),
        "shipment_id": str(decision.shipment_id),
        "run_id": str(decision.verification_run_id),
        "decision": decision.disposition,
        "reason_codes": reason_codes,
        "reasons": reasons,
        "policy_version": decision.policy_version,
        "actor_type": decision.actor_type,
        "decided_at": decision.decided_at.isoformat(),
    }
    summary = (
        f"Document {document_id} decision is {decision.disposition}"
        + (f" ({reason_codes[0]})" if reason_codes else "")
        + "."
    )
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary=summary,
        records=[record],
        citations=[
            QueryCitation(
                type="decision",
                id=str(decision.decision_id),
                decision_id=str(decision.decision_id),
                document_id=str(document_id),
                shipment_id=str(decision.shipment_id),
                run_id=str(decision.verification_run_id),
                code=decision.disposition,
            )
        ],
    )


def _list_shipments_by_decision(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    decided_after, decided_before, window_note = _parse_time_window(parameters)
    disposition = str(parameters.get("decision", "")).upper()

    rows = repository.shipments_by_decision(
        customer_id,
        disposition,
        limit=max_results,
        decided_after=decided_after,
        decided_before=decided_before,
    )
    # Deduplicate shipments (latest decision already ordered).
    seen: set[UUID] = set()
    records: list[dict[str, Any]] = []
    citations: list[QueryCitation] = []
    for shipment, decision in rows:
        if shipment.shipment_id in seen:
            continue
        seen.add(shipment.shipment_id)
        document_ids = [str(doc.document_id) for doc in shipment.documents]
        records.append(
            {
                "type": "shipment",
                "shipment_id": str(shipment.shipment_id),
                "decision": decision.disposition,
                "decision_id": str(decision.decision_id),
                "document_ids": document_ids,
                "decided_at": decision.decided_at.isoformat(),
            }
        )
        citations.append(
            QueryCitation(
                type="decision",
                id=str(decision.decision_id),
                decision_id=str(decision.decision_id),
                shipment_id=str(shipment.shipment_id),
                document_id=str(decision.document_id),
                code=decision.disposition,
            )
        )
    if not records:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"No shipments are in {disposition}{window_note}.",
            records=[],
            citations=[],
        )
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary=f"{len(records)} shipment(s) are in {disposition}{window_note}.",
        records=records,
        citations=citations,
    )


def _parse_time_window(
    parameters: dict[str, Any],
) -> tuple[Any, Any, str]:
    from datetime import UTC, datetime, timedelta

    updated_after = None
    updated_before = None
    time_range = parameters.get("time_range")
    if isinstance(time_range, dict):
        start = time_range.get("start") or time_range.get("from")
        end = time_range.get("end") or time_range.get("to")
        if isinstance(start, str) and start.strip():
            updated_after = datetime.fromisoformat(start.replace("Z", "+00:00"))
        if isinstance(end, str) and end.strip():
            updated_before = datetime.fromisoformat(end.replace("Z", "+00:00"))
        preset = str(time_range.get("preset") or "").lower()
        now = datetime.now(UTC)
        if updated_after is None:
            if preset in {"this_week", "week", "last_7_days", "7d"}:
                updated_after = now - timedelta(days=7)
                updated_before = now + timedelta(seconds=1)
            elif preset in {"today", "this_day"}:
                updated_after = now.replace(hour=0, minute=0, second=0, microsecond=0)
                updated_before = now + timedelta(seconds=1)
            elif preset in {"this_month", "month", "last_30_days", "30d"}:
                updated_after = now - timedelta(days=30)
                updated_before = now + timedelta(seconds=1)
    window_note = ""
    if updated_after is not None or updated_before is not None:
        window_note = " in the requested time window"
    return updated_after, updated_before, window_note


def _count_documents_by_agreement(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    del max_results
    agreement = str(parameters.get("agreement", "")).upper()
    updated_after, updated_before, window_note = _parse_time_window(parameters)
    count = repository.count_documents_by_agreement(
        customer_id,
        agreement,
        updated_after=updated_after,
        updated_before=updated_before,
    )
    if count == 0:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"0 documents have {agreement}{window_note}.",
            records=[],
            citations=[],
        )
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary=f"{count} documents have {agreement}{window_note}.",
        records=[
            {
                "type": "agreement_count",
                "agreement": agreement,
                "count": count,
            }
        ],
        citations=[],
    )


def _list_documents_by_agreement(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    agreement = str(parameters.get("agreement", "")).upper()
    updated_after, updated_before, window_note = _parse_time_window(parameters)
    rows = repository.documents_by_agreement(
        customer_id,
        agreement,
        limit=max_results,
        updated_after=updated_after,
        updated_before=updated_before,
    )
    if not rows:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"No documents have {agreement}{window_note}.",
            records=[],
            citations=[],
        )
    records, citations, lines = _agreement_row_payload(
        rows,
        header=(
            f"{len(rows)} document(s) with "
            f"{agreement.replace('_', ' ').lower()}{window_note}:"
        ),
        customer_id=customer_id,
        repository=repository,
    )
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary="\n".join(lines),
        records=records,
        citations=citations,
    )


def _count_documents_requiring_attention(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    del max_results
    updated_after, updated_before, window_note = _parse_time_window(parameters)
    count = repository.count_documents_requiring_attention(
        customer_id,
        updated_after=updated_after,
        updated_before=updated_before,
    )
    if count == 0:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"0 documents require attention{window_note}.",
            records=[],
            citations=[],
        )
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary=f"{count} documents require attention{window_note}.",
        records=[{"type": "attention_count", "count": count}],
        citations=[],
    )


def _count_documents_by_decision(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    del max_results
    disposition = str(parameters.get("decision", "")).upper()
    updated_after, updated_before, window_note = _parse_time_window(parameters)
    count = repository.count_documents_by_decision(
        customer_id,
        disposition,
        decided_after=updated_after,
        decided_before=updated_before,
    )
    if count == 0:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"0 documents were {disposition}{window_note}.",
            records=[],
            citations=[],
        )
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary=f"{count} documents were {disposition}{window_note}.",
        records=[
            {
                "type": "decision_count",
                "decision": disposition,
                "count": count,
            }
        ],
        citations=[],
    )


def _count_documents_with_mismatches(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    del max_results
    updated_after, updated_before, window_note = _parse_time_window(parameters)
    count = repository.count_documents_with_mismatches(
        customer_id,
        updated_after=updated_after,
        updated_before=updated_before,
    )
    if count == 0:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"0 documents have mismatches{window_note}.",
            records=[],
            citations=[],
        )
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary=f"{count} documents have mismatches{window_note}.",
        records=[{"type": "mismatch_count", "count": count}],
        citations=[],
    )


def _list_documents_for_shipment(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    shipment_id = _parse_uuid(parameters, "shipment_id")
    shipment = repository.shipment_for_customer(customer_id, shipment_id)
    if shipment is None:
        raise MissingEntityError("shipment", str(shipment_id))
    documents = repository.documents_for_shipment(customer_id, shipment_id)[:max_results]
    if not documents:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"Shipment {shipment_id} has no documents.",
            records=[],
            citations=[
                QueryCitation(
                    type="shipment",
                    id=str(shipment_id),
                    shipment_id=str(shipment_id),
                )
            ],
        )
    records = [
        {
            "type": "document",
            "document_id": str(doc.document_id),
            "shipment_id": str(shipment_id),
            "document_type": repository.document_type_wire(doc.document_type),
            "status": repository.document_status_wire(doc.status),
        }
        for doc in documents
    ]
    citations = [
        QueryCitation(
            type="document",
            id=str(doc.document_id),
            document_id=str(doc.document_id),
            shipment_id=str(shipment_id),
        )
        for doc in documents
    ]
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary=f"Shipment {shipment_id} has {len(records)} document(s).",
        records=records,
        citations=citations,
    )


_SOURCE_NOTE = "Source: persisted Nova document/validation/decision records."


def _confidence_text(percent: int | None) -> str:
    return f"{percent}%" if percent is not None else "Confidence unavailable"


def _agreement_row_payload(
    rows: list[Any],
    *,
    header: str,
    customer_id: UUID,
    repository: QueryRepository,
) -> tuple[list[dict[str, Any]], list[QueryCitation], list[str]]:
    """Shared grounded projection for document lists carrying agreement data."""
    records: list[dict[str, Any]] = []
    citations: list[QueryCitation] = []
    lines: list[str] = [header]
    for document, agreement, decision, invoice_number in rows:
        validation = repository.validation_for_document(customer_id, document.document_id)
        validation_text = validation.aggregate_result if validation else "—"
        percent = agreement.document_confidence_percent
        records.append(
            {
                "type": "document",
                "document_id": str(document.document_id),
                "shipment_id": str(document.shipment_id),
                "invoice_number": invoice_number,
                "agreement": agreement.category.value,
                "document_confidence": agreement.document_confidence,
                "document_confidence_percent": percent,
                "extraction_confidence": agreement.extraction_confidence,
                "extraction_confidence_percent": agreement.extraction_confidence_percent,
                "decision": decision.disposition if decision else None,
                "validation_result": validation.aggregate_result if validation else None,
                "status": repository.document_status_wire(document.status),
                "updated_at": document.updated_at.isoformat(),
            }
        )
        citations.append(
            QueryCitation(
                type="document",
                id=str(document.document_id),
                document_id=str(document.document_id),
                shipment_id=str(document.shipment_id),
                code=agreement.category.value,
            )
        )
        label = invoice_number or str(document.document_id)
        decision_text = decision.disposition if decision else "—"
        lines.append(f"- {label} — {_confidence_text(percent)} — {decision_text}")
        lines.append(
            f"  Agreement: {agreement.category.value}; Validation: {validation_text}; "
            f"Confidence: {_confidence_text(percent)} "
            f"(extraction {_confidence_text(agreement.extraction_confidence_percent)})"
        )
    lines.append(_SOURCE_NOTE)
    return records, citations, lines


def _count_documents(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    del max_results
    after, before, window_note = _parse_time_window(parameters)
    count = repository.count_documents(
        customer_id,
        updated_after=after,
        updated_before=before,
    )
    summary = f"There are {count} document(s){window_note}. {_SOURCE_NOTE}"
    status = QueryStatus.EMPTY if count == 0 else QueryStatus.RESULT
    return status, QueryResultPayload(
        answer_summary=summary,
        records=[{"type": "document_count", "count": count}],
        citations=[],
    )


def _count_shipments(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    del max_results
    after, before, window_note = _parse_time_window(parameters)
    count = repository.count_shipments(
        customer_id,
        updated_after=after,
        updated_before=before,
    )
    summary = f"There are {count} shipment(s){window_note}. {_SOURCE_NOTE}"
    status = QueryStatus.EMPTY if count == 0 else QueryStatus.RESULT
    return status, QueryResultPayload(
        answer_summary=summary,
        records=[{"type": "shipment_count", "count": count}],
        citations=[],
    )


def _list_shipments(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    after, before, window_note = _parse_time_window(parameters)
    shipments = repository.shipments_for_customer(
        customer_id,
        limit=max_results,
        updated_after=after,
        updated_before=before,
    )
    if not shipments:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"There are currently 0 shipments{window_note}.",
            records=[],
            citations=[],
        )
    records = [
        {
            "type": "shipment",
            "shipment_id": str(shipment.shipment_id),
            "status": shipment.status,
            "document_count": len(shipment.documents),
            "updated_at": shipment.updated_at.isoformat(),
        }
        for shipment in shipments
    ]
    citations = [
        QueryCitation(
            type="shipment",
            id=str(shipment.shipment_id),
            shipment_id=str(shipment.shipment_id),
        )
        for shipment in shipments
    ]
    lines = [f"{len(records)} shipment(s){window_note}:"]
    for shipment in shipments:
        lines.append(
            f"- {shipment.shipment_id} — {shipment.status} — "
            f"{len(shipment.documents)} document(s)"
        )
    lines.append(_SOURCE_NOTE)
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary="\n".join(lines),
        records=records,
        citations=citations,
    )


def _list_recent_documents(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    after, before, window_note = _parse_time_window(parameters)
    rows = repository.recent_documents(
        customer_id,
        limit=max_results,
        updated_after=after,
        updated_before=before,
    )
    if not rows:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"There are currently 0 documents{window_note}.",
            records=[],
            citations=[],
        )
    records, citations, lines = _agreement_row_payload(
        rows,
        header=f"{len(rows)} most recent document(s){window_note}:",
        customer_id=customer_id,
        repository=repository,
    )
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary="\n".join(lines),
        records=records,
        citations=citations,
    )


def _list_documents_by_confidence(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    after, before, _window_note = _parse_time_window(parameters)
    order = str(parameters.get("order") or "").lower()

    if order == "lowest":
        rows = repository.documents_by_lowest_confidence(customer_id, limit=max_results)
        header = f"{len(rows)} document(s) with the lowest agreement confidence:"
        if not rows:
            return QueryStatus.EMPTY, QueryResultPayload(
                answer_summary="There are currently 0 documents to rank by confidence.",
                records=[],
                citations=[],
            )
    else:
        threshold = _confidence_threshold(parameters)
        rows = repository.documents_below_confidence(
            customer_id,
            threshold,
            limit=max_results,
            updated_after=after,
            updated_before=before,
        )
        percent = int(round(threshold * 100))
        if not rows:
            return QueryStatus.EMPTY, QueryResultPayload(
                answer_summary=(
                    f"There are currently 0 documents with confidence below {percent}%."
                ),
                records=[],
                citations=[],
            )
        header = f"{len(rows)} document(s) with confidence below {percent}%:"

    records, citations, lines = _agreement_row_payload(
        rows,
        header=header,
        customer_id=customer_id,
        repository=repository,
    )
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary="\n".join(lines),
        records=records,
        citations=citations,
    )


def _confidence_threshold(parameters: dict[str, Any]) -> float:
    raw = parameters.get("max_confidence")
    if raw is None:
        return 0.70
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.70
    if value > 1.0:
        value = value / 100.0
    return min(max(value, 0.0), 1.0)


def _list_documents_by_decision(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    disposition = str(parameters.get("decision", "")).upper()
    after, before, window_note = _parse_time_window(parameters)
    rows = repository.documents_by_decision(
        customer_id,
        disposition,
        limit=max_results,
        decided_after=after,
        decided_before=before,
    )
    if not rows:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"There are currently 0 documents in {disposition}{window_note}.",
            records=[],
            citations=[],
        )
    records: list[dict[str, Any]] = []
    citations: list[QueryCitation] = []
    lines = [f"{len(rows)} document(s) in {disposition}{window_note}:"]
    for document, decision in rows:
        agreement_row = repository.agreement_for_document_id(customer_id, document.document_id)
        percent = agreement_row[1].document_confidence_percent if agreement_row else None
        invoice_number = agreement_row[3] if agreement_row else None
        label = invoice_number or str(document.document_id)
        reason_codes = list(decision.reason_codes or [])
        records.append(
            {
                "type": "document",
                "document_id": str(document.document_id),
                "shipment_id": str(document.shipment_id),
                "invoice_number": invoice_number,
                "decision": decision.disposition,
                "decision_id": str(decision.decision_id),
                "reason_codes": reason_codes,
                "document_confidence_percent": percent,
                "agreement": agreement_row[1].category.value if agreement_row else None,
                "decided_at": decision.decided_at.isoformat(),
            }
        )
        citations.append(
            QueryCitation(
                type="decision",
                id=str(decision.decision_id),
                decision_id=str(decision.decision_id),
                document_id=str(document.document_id),
                shipment_id=str(document.shipment_id),
                code=decision.disposition,
            )
        )
        primary = reason_codes[0] if reason_codes else "—"
        lines.append(
            f"- {label} — {_confidence_text(percent)} — {decision.disposition} ({primary})"
        )
    lines.append(_SOURCE_NOTE)
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary="\n".join(lines),
        records=records,
        citations=citations,
    )


def _list_documents_by_validation(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
    aggregate_result: str,
    label: str,
) -> tuple[QueryStatus, QueryResultPayload]:
    after, before, window_note = _parse_time_window(parameters)
    rows = repository.documents_by_validation_result(
        customer_id,
        aggregate_result,
        limit=max_results,
        updated_after=after,
        updated_before=before,
    )
    if not rows:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"There are currently 0 documents with {label}{window_note}.",
            records=[],
            citations=[],
        )
    records: list[dict[str, Any]] = []
    citations: list[QueryCitation] = []
    lines = [f"{len(rows)} document(s) with {label}{window_note}:"]
    for document, validation in rows:
        agreement_row = repository.agreement_for_document_id(customer_id, document.document_id)
        invoice_number = agreement_row[3] if agreement_row else None
        percent = agreement_row[1].document_confidence_percent if agreement_row else None
        failing = repository.failing_checks(validation)
        mismatched = [item["field"] for item in failing if item["result"] == "MISMATCH"]
        uncertain = [item["field"] for item in failing if item["result"] == "UNCERTAIN"]
        records.append(
            {
                "type": "document",
                "document_id": str(document.document_id),
                "shipment_id": str(document.shipment_id),
                "invoice_number": invoice_number,
                "validation_id": str(validation.validation_id),
                "validation_result": validation.aggregate_result,
                "mismatched_fields": mismatched,
                "uncertain_fields": uncertain,
                "document_confidence_percent": percent,
                "agreement": agreement_row[1].category.value if agreement_row else None,
            }
        )
        citations.append(
            QueryCitation(
                type="validation",
                id=str(validation.validation_id),
                validation_id=str(validation.validation_id),
                document_id=str(document.document_id),
                shipment_id=str(document.shipment_id),
                code=validation.aggregate_result,
            )
        )
        name = invoice_number or str(document.document_id)
        detail = mismatched if aggregate_result == "MISMATCH" else uncertain
        shown = ", ".join(str(field) for field in detail[:5]) if detail else "—"
        lines.append(f"- {name} — {_confidence_text(percent)} — {len(detail)} field(s): {shown}")
    lines.append(_SOURCE_NOTE)
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary="\n".join(lines),
        records=records,
        citations=citations,
    )


def _list_documents_with_mismatches(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    return _list_documents_by_validation(
        parameters,
        customer_id=customer_id,
        repository=repository,
        max_results=max_results,
        aggregate_result="MISMATCH",
        label="validation mismatches",
    )


def _list_documents_with_uncertain_validation(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    return _list_documents_by_validation(
        parameters,
        customer_id=customer_id,
        repository=repository,
        max_results=max_results,
        aggregate_result="UNCERTAIN",
        label="uncertain validation",
    )


def _resolve_document_row(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
) -> Any:
    """Resolve a document from an explicit id or a human reference."""
    raw_id = parameters.get("document_id")
    if raw_id is not None:
        document_id = UUID(str(raw_id))
        row = repository.agreement_for_document_id(customer_id, document_id)
        if row is None:
            raise MissingEntityError("document", str(document_id))
        return row

    reference = parameters.get("document_ref")
    if reference is None:
        raise ValueError("missing parameter document_id")
    matches = repository.resolve_document_reference(customer_id, str(reference))
    if not matches:
        raise MissingEntityError("document", str(reference))
    return matches[0]


def _get_document_mismatched_fields(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    del max_results
    document, agreement, _decision, invoice_number = _resolve_document_row(
        parameters,
        customer_id=customer_id,
        repository=repository,
    )
    label = invoice_number or str(document.document_id)
    validation = repository.validation_for_document(customer_id, document.document_id)
    if validation is None:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"No validation record exists for {label}.",
            records=[],
            citations=[],
        )
    mismatched = repository.mismatched_checks(validation)
    if not mismatched:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=(
                f"{label} has 0 mismatched fields "
                f"(validation result {validation.aggregate_result}). {_SOURCE_NOTE}"
            ),
            records=[],
            citations=[],
        )
    lines = [f"{label} has {len(mismatched)} mismatched field(s):"]
    citations: list[QueryCitation] = []
    for item in mismatched:
        detail = item.get("reason_detail") or item.get("reason_code") or "—"
        lines.append(f"- {item['field']} — {item['rule_key'] or item['reason_code']} — {detail}")
        citations.append(
            QueryCitation(
                type="validation_check",
                id=item["check_id"],
                validation_id=str(validation.validation_id),
                document_id=str(document.document_id),
                field=item["field"],
                code=item["reason_code"],
            )
        )
    lines.append(_SOURCE_NOTE)
    record = {
        "type": "mismatched_fields",
        "document_id": str(document.document_id),
        "invoice_number": invoice_number,
        "validation_id": str(validation.validation_id),
        "validation_result": validation.aggregate_result,
        "mismatch_count": len(mismatched),
        "mismatches": mismatched,
        "agreement": agreement.category.value,
        "document_confidence_percent": agreement.document_confidence_percent,
    }
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary="\n".join(lines),
        records=[record],
        citations=citations,
    )


def _explain_document_review(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    del max_results
    document, agreement, decision, invoice_number = _resolve_document_row(
        parameters,
        customer_id=customer_id,
        repository=repository,
    )
    label = invoice_number or str(document.document_id)
    validation = repository.validation_for_document(customer_id, document.document_id)
    if decision is None:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"No decision record exists for {label}.",
            records=[],
            citations=[],
        )

    reason_codes = list(decision.reason_codes or [])
    constraints = list(decision.safety_constraints_applied or [])
    failing = repository.failing_checks(validation) if validation is not None else []
    mismatched = [item for item in failing if item["result"] == "MISMATCH"]
    uncertain = [item for item in failing if item["result"] == "UNCERTAIN"]

    lines = [f"{label} was routed to {decision.disposition}."]
    lines.append(
        f"Agreement: {agreement.category.value} "
        f"({_confidence_text(agreement.document_confidence_percent)}); "
        f"extraction confidence {_confidence_text(agreement.extraction_confidence_percent)}."
    )
    if validation is not None:
        lines.append(
            f"Validation result: {validation.aggregate_result} — "
            f"{len(mismatched)} mismatch(es), {len(uncertain)} uncertain."
        )
    if reason_codes:
        lines.append(f"Router reason codes: {', '.join(reason_codes)}.")
    if constraints:
        lines.append(f"Safety constraints applied: {', '.join(constraints)}.")
    if mismatched:
        lines.append("Mismatched fields:")
        for item in mismatched[:10]:
            lines.append(f"- {item['field']} — {item.get('reason_detail') or item['reason_code']}")
    if uncertain:
        lines.append("Uncertain fields:")
        for item in uncertain[:10]:
            lines.append(f"- {item['field']} — {item.get('reason_detail') or item['reason_code']}")
    lines.append(_SOURCE_NOTE)

    record = {
        "type": "review_explanation",
        "document_id": str(document.document_id),
        "invoice_number": invoice_number,
        "decision": decision.disposition,
        "decision_id": str(decision.decision_id),
        "reason_codes": reason_codes,
        "safety_constraints_applied": constraints,
        "rationale": decision.llm_rationale,
        "agreement": agreement.category.value,
        "document_confidence_percent": agreement.document_confidence_percent,
        "extraction_confidence_percent": agreement.extraction_confidence_percent,
        "validation_result": validation.aggregate_result if validation else None,
        "mismatched_fields": [item["field"] for item in mismatched],
        "uncertain_fields": [item["field"] for item in uncertain],
    }
    citations = [
        QueryCitation(
            type="decision",
            id=str(decision.decision_id),
            decision_id=str(decision.decision_id),
            document_id=str(document.document_id),
            shipment_id=str(document.shipment_id),
            code=decision.disposition,
        )
    ]
    if validation is not None:
        citations.append(
            QueryCitation(
                type="validation",
                id=str(validation.validation_id),
                validation_id=str(validation.validation_id),
                document_id=str(document.document_id),
                code=validation.aggregate_result,
            )
        )
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary="\n".join(lines),
        records=[record],
        citations=citations,
    )


def _compare_agreement(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    del max_results
    after, before, window_note = _parse_time_window(parameters)
    breakdown = repository.agreement_breakdown(
        customer_id,
        updated_after=after,
        updated_before=before,
    )
    total = sum(breakdown.values())
    if total == 0:
        return QueryStatus.EMPTY, QueryResultPayload(
            answer_summary=f"There are currently 0 classified documents{window_note}.",
            records=[],
            citations=[],
        )
    lines = [f"Agreement breakdown across {total} document(s){window_note}:"]
    for category, count in breakdown.items():
        share = int(round((count / total) * 100))
        lines.append(f"- {category}: {count} ({share}%)")
    lines.append(_SOURCE_NOTE)
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary="\n".join(lines),
        records=[
            {
                "type": "agreement_breakdown",
                "total": total,
                "counts": dict(breakdown),
            }
        ],
        citations=[],
    )


def _summarize_run(
    parameters: dict[str, Any],
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    del max_results
    run_id = _parse_uuid(parameters, "run_id")
    run = repository.run_for_customer(customer_id, run_id)
    if run is None:
        raise MissingEntityError("run", str(run_id))
    fields = repository.extracted_fields_for_run(run_id)
    validation = repository.validation_for_run(run_id)
    decision = repository.decision_for_run(run_id)
    field_records = [
        {
            "field": row.field_key,
            "value": row.value_json,
            "presence": row.presence,
            "confidence": row.confidence,
            "is_missing": row.is_missing,
        }
        for row in fields
    ]
    record: dict[str, Any] = {
        "type": "run_summary",
        "run_id": str(run.verification_run_id),
        "shipment_id": str(run.shipment_id),
        "run_status": run.status,
        "extracted_field_count": len(fields),
        "extracted_fields": field_records,
        "validation": None,
        "decision": None,
    }
    citations = [
        QueryCitation(
            type="run",
            id=str(run.verification_run_id),
            run_id=str(run.verification_run_id),
            shipment_id=str(run.shipment_id),
        )
    ]
    if validation is not None:
        record["validation"] = {
            "validation_id": str(validation.validation_id),
            "overall_result": validation.aggregate_result,
            "status": validation.status,
        }
        citations.append(
            QueryCitation(
                type="validation",
                id=str(validation.validation_id),
                validation_id=str(validation.validation_id),
                run_id=str(run_id),
                code=validation.aggregate_result,
            )
        )
    if decision is not None:
        record["decision"] = {
            "decision_id": str(decision.decision_id),
            "decision": decision.disposition,
            "reason_codes": list(decision.reason_codes or []),
        }
        citations.append(
            QueryCitation(
                type="decision",
                id=str(decision.decision_id),
                decision_id=str(decision.decision_id),
                run_id=str(run_id),
                code=decision.disposition,
            )
        )
    parts = [f"Run {run_id} status is {run.status}"]
    parts.append(f"{len(fields)} extracted field(s)")
    if validation is not None:
        parts.append(f"validation={validation.aggregate_result}")
    else:
        parts.append("validation=absent")
    if decision is not None:
        parts.append(f"decision={decision.disposition}")
    else:
        parts.append("decision=absent")
    return QueryStatus.RESULT, QueryResultPayload(
        answer_summary="; ".join(parts) + ".",
        records=[record],
        citations=citations,
    )
