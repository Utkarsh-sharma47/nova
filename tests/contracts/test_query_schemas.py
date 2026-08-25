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
    }


def test_unsupported_reason_codes() -> None:
    assert UnsupportedReasonCode.SECURITY_REJECTED.value == "SECURITY_REJECTED"
