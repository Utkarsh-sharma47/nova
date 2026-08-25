"""Allow-listed intent executors grounded in QueryRepository results."""

from __future__ import annotations

from typing import Any
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


def execute_intent(
    intent: InterpretedIntent,
    *,
    customer_id: UUID,
    repository: QueryRepository,
    max_results: int,
) -> tuple[QueryStatus, QueryResultPayload]:
    handlers = {
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
    }
    handler = handlers[intent.name]
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
    records: list[dict[str, Any]] = []
    citations: list[QueryCitation] = []
    lines: list[str] = [f"{agreement.replace('_', ' ').title()} documents{window_note}:"]
    for document, result, decision, invoice_number in rows:
        label = invoice_number or str(document.document_id)
        confidence_pct = result.document_confidence_percent
        confidence_text = (
            f"{confidence_pct}%" if confidence_pct is not None else "Confidence unavailable"
        )
        decision_text = decision.disposition if decision else "—"
        validation = repository.validation_for_document(customer_id, document.document_id)
        validation_text = validation.aggregate_result if validation else "—"
        records.append(
            {
                "type": "document",
                "document_id": str(document.document_id),
                "shipment_id": str(document.shipment_id),
                "invoice_number": invoice_number,
                "agreement": result.category.value,
                "document_confidence": result.document_confidence,
                "document_confidence_percent": confidence_pct,
                "decision": decision.disposition if decision else None,
                "validation_result": validation.aggregate_result if validation else None,
            }
        )
        citations.append(
            QueryCitation(
                type="document",
                id=str(document.document_id),
                document_id=str(document.document_id),
                shipment_id=str(document.shipment_id),
                code=result.category.value,
            )
        )
        lines.append(f"- {label}")
        lines.append(f"  Confidence: {confidence_text}")
        lines.append(f"  Agreement: {result.category.value}")
        lines.append(f"  Decision: {decision_text}")
        lines.append(f"  Validation: {validation_text}")
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
