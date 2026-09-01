"""Application service for grounded natural-language query."""

from __future__ import annotations

import logging
import time

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from nova.contracts.query import (
    InterpretedIntent,
    QueryFailurePayload,
    QueryRequest,
    QueryResponse,
    QueryResultPayload,
    QueryStatus,
    UnsupportedPayload,
    UnsupportedReasonCode,
)
from nova.llm.errors import LLMError, LLMTimeoutError
from nova.llm.port import LLMPort
from nova.query.classifier import classify_intent
from nova.query.executors import (
    AmbiguousReferenceError,
    MissingEntityError,
    execute_intent,
)
from nova.query.repository import QueryRepository

logger = logging.getLogger("nova.query")

_MAX_RESULTS_CAP = 50


class QueryService:
    """question → intent → controlled repository read → grounded response."""

    def __init__(
        self,
        session: Session,
        *,
        llm: LLMPort | None = None,
    ) -> None:
        self.session = session
        self.llm = llm
        self.repository = QueryRepository(session)

    def answer(self, request: QueryRequest, *, trace_id: str) -> QueryResponse:
        started = time.perf_counter()
        try:
            outcome = classify_intent(request, self.llm)
        except LLMTimeoutError:
            return self._failure(
                request,
                trace_id,
                code="AI_PROVIDER_TIMEOUT",
                message="Query interpretation timed out.",
                retryable=True,
            )
        except LLMError:
            return self._failure(
                request,
                trace_id,
                code="AI_PROVIDER_ERROR",
                message="Query interpretation temporarily unavailable.",
                retryable=True,
            )

        if outcome.unsupported is not None:
            self._log(request, trace_id, None, QueryStatus.UNSUPPORTED, started)
            return QueryResponse(
                question=request.question,
                interpreted_intent=None,
                status=QueryStatus.UNSUPPORTED,
                unsupported=outcome.unsupported,
                trace_id=trace_id,
            )

        assert outcome.intent is not None
        intent = outcome.intent
        max_results = min(request.options.max_results, _MAX_RESULTS_CAP)
        try:
            status, payload = execute_intent(
                intent,
                customer_id=request.customer_id,
                repository=self.repository,
                max_results=max_results,
            )
        except AmbiguousReferenceError as exc:
            self._log(request, trace_id, intent.name.value, QueryStatus.UNSUPPORTED, started)
            return QueryResponse(
                question=request.question,
                interpreted_intent=intent,
                status=QueryStatus.UNSUPPORTED,
                unsupported=UnsupportedPayload(
                    reason_code=UnsupportedReasonCode.AMBIGUOUS_INTENT,
                    message=(
                        f'"{exc.reference}" matches {len(exc.candidates)} documents. '
                        "Ask again naming one of them."
                    ),
                    suggestions=[f"Ask about {candidate}" for candidate in exc.candidates],
                ),
                trace_id=trace_id,
            )
        except MissingEntityError as exc:
            self._log(request, trace_id, intent.name.value, QueryStatus.EMPTY, started)
            return QueryResponse(
                question=request.question,
                interpreted_intent=intent,
                status=QueryStatus.EMPTY,
                result=QueryResultPayload(
                    answer_summary=f"No matching {exc.entity} found for id {exc.entity_id}.",
                    records=[],
                    citations=[],
                ),
                trace_id=trace_id,
            )
        except (ValueError, KeyError) as exc:
            self._log(request, trace_id, intent.name.value, QueryStatus.UNSUPPORTED, started)
            return QueryResponse(
                question=request.question,
                interpreted_intent=intent,
                status=QueryStatus.UNSUPPORTED,
                unsupported=UnsupportedPayload(
                    reason_code=UnsupportedReasonCode.MISSING_SCOPE_ID,
                    message=str(exc),
                    suggestions=[
                        "Provide shipment_id, document_id, or run_id in scope",
                    ],
                ),
                trace_id=trace_id,
            )
        except SQLAlchemyError:
            logger.exception(
                "query_database_failure",
                extra={
                    "event": "query.database_failure",
                    "trace_id": trace_id,
                    "customer_id": str(request.customer_id),
                },
            )
            return self._failure(
                request,
                trace_id,
                code="DATABASE_ERROR",
                message="Query persistence layer is temporarily unavailable.",
                retryable=True,
                intent=intent,
            )

        self._log(request, trace_id, intent.name.value, status, started)
        return QueryResponse(
            question=request.question,
            interpreted_intent=intent,
            status=status,
            result=payload,
            trace_id=trace_id,
        )

    def _failure(
        self,
        request: QueryRequest,
        trace_id: str,
        *,
        code: str,
        message: str,
        retryable: bool,
        intent: InterpretedIntent | None = None,
    ) -> QueryResponse:
        return QueryResponse(
            question=request.question,
            interpreted_intent=intent,
            status=QueryStatus.FAILURE,
            failure=QueryFailurePayload(code=code, message=message, retryable=retryable),
            trace_id=trace_id,
        )

    def _log(
        self,
        request: QueryRequest,
        trace_id: str,
        intent_name: str | None,
        status: QueryStatus,
        started: float,
    ) -> None:
        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "query_completed",
            extra={
                "event": "query.completed",
                "trace_id": trace_id,
                "customer_id": str(request.customer_id),
                "intent": intent_name,
                "status": status.value,
                "latency_ms": latency_ms,
            },
        )

