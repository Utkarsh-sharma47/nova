"""Natural-language query contracts for POST /v1/query (REQ-QUERY-001–003)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QueryIntentName(StrEnum):
    """Part 1 allow-listed intents. The LLM may classify among these only."""

    GET_SHIPMENT = "get_shipment"
    GET_DOCUMENT = "get_document"
    GET_DOCUMENT_VALIDATION = "get_document_validation"
    GET_DOCUMENT_DECISION = "get_document_decision"
    LIST_SHIPMENTS_BY_DECISION = "list_shipments_by_decision"
    LIST_DOCUMENTS_FOR_SHIPMENT = "list_documents_for_shipment"
    SUMMARIZE_RUN = "summarize_run"
    COUNT_DOCUMENTS_BY_AGREEMENT = "count_documents_by_agreement"
    LIST_DOCUMENTS_BY_AGREEMENT = "list_documents_by_agreement"
    COUNT_DOCUMENTS_REQUIRING_ATTENTION = "count_documents_requiring_attention"
    COUNT_DOCUMENTS_BY_DECISION = "count_documents_by_decision"
    COUNT_DOCUMENTS_WITH_MISMATCHES = "count_documents_with_mismatches"


class QueryStatus(StrEnum):
    RESULT = "RESULT"
    EMPTY = "EMPTY"
    UNSUPPORTED = "UNSUPPORTED"
    FAILURE = "FAILURE"


class UnsupportedReasonCode(StrEnum):
    INTENT_NOT_SUPPORTED = "INTENT_NOT_SUPPORTED"
    AMBIGUOUS_INTENT = "AMBIGUOUS_INTENT"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    MISSING_SCOPE_ID = "MISSING_SCOPE_ID"
    SECURITY_REJECTED = "SECURITY_REJECTED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"


class QueryScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shipment_id: UUID | None = None
    document_id: UUID | None = None
    run_id: UUID | None = None
    time_range: dict[str, Any] | None = None


class QueryOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_results: int = Field(default=20, ge=1, le=100)


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)
    customer_id: UUID
    scope: QueryScope = Field(default_factory=QueryScope)
    options: QueryOptions = Field(default_factory=QueryOptions)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("question must not be blank")
        return cleaned


class InterpretedIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: QueryIntentName
    version: str = "1"
    parameters: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class QueryCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    id: str | None = None
    shipment_id: str | None = None
    document_id: str | None = None
    validation_id: str | None = None
    decision_id: str | None = None
    run_id: str | None = None
    field: str | None = None
    code: str | None = None


class QueryResultPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_summary: str
    records: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[QueryCitation] = Field(default_factory=list)


class UnsupportedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason_code: UnsupportedReasonCode
    message: str
    suggestions: list[str] = Field(default_factory=list)


class QueryFailurePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    retryable: bool = False


class QueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    interpreted_intent: InterpretedIntent | None = None
    status: QueryStatus
    result: QueryResultPayload | None = None
    unsupported: UnsupportedPayload | None = None
    failure: QueryFailurePayload | None = None
    trace_id: str
