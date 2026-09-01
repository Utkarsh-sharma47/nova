from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from nova.contracts.query import (
    QueryIntentName,
    QueryRequest,
    QueryResponse,
    QueryStatus,
    UnsupportedReasonCode,
)


def test_query_request_schema() -> None:
    request = QueryRequest(
        question="Which shipments are waiting on human review?",
        customer_id=uuid4(),
    )
    assert request.options.max_results == 20


def test_query_request_rejects_blank() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(question="  ", customer_id=uuid4())


def test_query_response_result_envelope() -> None:
    response = QueryResponse(
        question="q",
        status=QueryStatus.RESULT,
        result={
            "answer_summary": "ok",
            "records": [],
            "citations": [],
        },
        trace_id="t1",
    )
    assert response.unsupported is None
    assert response.failure is None


def test_intent_allow_list_values() -> None:
    names = {item.value for item in QueryIntentName}
    assert names == {
        "get_shipment",
        "get_document",
        "get_document_validation",
        "get_document_decision",
        "list_shipments_by_decision",
        "list_documents_for_shipment",
        "summarize_run",
        "count_documents_by_agreement",
        "list_documents_by_agreement",
        "count_documents_requiring_attention",
        "count_documents_by_decision",
        "count_documents_with_mismatches",
        "count_documents",
        "count_shipments",
        "list_shipments",
        "list_recent_documents",
        "list_documents_by_decision",
        "list_documents_by_confidence",
        "list_documents_with_mismatches",
        "list_documents_with_uncertain_validation",
        "get_document_mismatched_fields",
        "explain_document_review",
        "compare_agreement",
    }


def test_every_intent_has_an_executor() -> None:
    """An allow-listed intent without a handler would raise KeyError at runtime."""
    from nova.query.executors import intent_handlers

    assert set(intent_handlers()) == set(QueryIntentName)


def test_unsupported_reason_codes() -> None:
    assert UnsupportedReasonCode.SECURITY_REJECTED.value == "SECURITY_REJECTED"
