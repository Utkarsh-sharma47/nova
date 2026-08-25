"""Security gate and intent classification for NL query (no SQL generation)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from nova.contracts.query import (
    InterpretedIntent,
    QueryIntentName,
    QueryRequest,
    QueryScope,
    UnsupportedPayload,
    UnsupportedReasonCode,
)
from nova.llm.errors import LLMError, LLMOutputError, LLMTimeoutError
from nova.llm.port import LLMPort, LLMRequest

logger = logging.getLogger("nova.query.classifier")

_MIN_LLM_CONFIDENCE = 0.55

_SQL_INJECTION = re.compile(
    r"(?i)\b(select|insert|update|delete|drop|alter|truncate|union|exec|execute|"
    r"grant|revoke|create\s+table|information_schema|pg_catalog|pg_sleep|"
    r"xp_cmdshell|load_file|into\s+outfile)\b|;--|/\*|\*/|;\s*$"
)
_PROMPT_INJECTION = re.compile(
    r"(?i)(ignore\s+(all\s+)?(previous|prior|above)\s+instructions|"
    r"system\s+prompt|reveal\s+(your\s+)?(system|hidden)\s+prompt|"
    r"jailbreak|developer\s+mode|do\s+anything\s+now|"
    r"override\s+(safety|policy)|exfiltrat)"
)
_SCHEMA_DISCOVERY = re.compile(
    r"(?i)(list\s+(all\s+)?(tables|columns|schemas)|show\s+(create\s+table|schema)|"
    r"describe\s+table|dump\s+(schema|database)|information_schema|"
    r"what\s+tables\s+(exist|do\s+you\s+have))"
)
_ARBITRARY_SQL = re.compile(
    r"(?i)(run\s+(this\s+)?sql|execute\s+(this\s+)?(query|sql)|"
    r"raw\s+sql|write\s+(me\s+)?(a\s+)?sql|generate\s+sql)"
)
_MUTATING_COMMAND = re.compile(
    r"(?i)\b(approve|reject|amend|delete|update|modify|send\s+email|"
    r"change\s+decision|set\s+status)\b"
)

_UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)

_DECISION_VALUES = {"AUTO_APPROVE", "HUMAN_REVIEW", "AMENDMENT_REQUEST"}

_SUGGESTIONS = [
    "Ask for a shipment or document by id",
    "Ask which shipments are in HUMAN_REVIEW",
    "Ask for validation or decision status for a document",
    "Ask which documents belong to a shipment",
]


@dataclass(frozen=True)
class ClassificationOutcome:
    intent: InterpretedIntent | None = None
    unsupported: UnsupportedPayload | None = None


def _unsupported(
    code: UnsupportedReasonCode,
    message: str,
    suggestions: list[str] | None = None,
) -> ClassificationOutcome:
    return ClassificationOutcome(
        unsupported=UnsupportedPayload(
            reason_code=code,
            message=message,
            suggestions=suggestions if suggestions is not None else list(_SUGGESTIONS),
        )
    )


def security_reject(question: str) -> ClassificationOutcome | None:
    """Reject questions that attempt SQL, schema discovery, or prompt abuse."""
    if _SQL_INJECTION.search(question) or _ARBITRARY_SQL.search(question):
        return _unsupported(
            UnsupportedReasonCode.SECURITY_REJECTED,
            "Nova does not execute arbitrary SQL or database commands from questions.",
            suggestions=[
                "Ask a supported business question about shipments or documents",
            ],
        )
    if _SCHEMA_DISCOVERY.search(question):
        return _unsupported(
            UnsupportedReasonCode.SECURITY_REJECTED,
            "Schema and catalog discovery are not available through the query interface.",
        )
    if _PROMPT_INJECTION.search(question):
        return _unsupported(
            UnsupportedReasonCode.SECURITY_REJECTED,
            "Prompt manipulation attempts are rejected; only allow-listed intents are answered.",
        )
    if _MUTATING_COMMAND.search(question) and re.search(
        r"(?i)\b(this|the)\s+(shipment|document|decision)\b",
        question,
    ):
        return _unsupported(
            UnsupportedReasonCode.OUT_OF_SCOPE,
            "Mutating commands are out of scope for Part 1 natural-language query.",
        )
    return None


def _uuid_from_text(question: str) -> UUID | None:
    match = _UUID_RE.search(question)
    if not match:
        return None
    return UUID(match.group(0))


def _decision_from_text(question: str) -> str | None:
    upper = question.upper()
    for value in _DECISION_VALUES:
        if value in upper:
            return value
    if re.search(r"(?i)human\s+review|waiting\s+on\s+(human\s+)?review", question):
        return "HUMAN_REVIEW"
    if re.search(r"(?i)auto[_\s-]?approv", question):
        return "AUTO_APPROVE"
    if re.search(r"(?i)amendment", question):
        return "AMENDMENT_REQUEST"
    return None


def _merge_scope(
    scope: QueryScope,
    *,
    shipment_id: UUID | None = None,
    document_id: UUID | None = None,
    run_id: UUID | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    sid = shipment_id or scope.shipment_id
    did = document_id or scope.document_id
    rid = run_id or scope.run_id
    if sid is not None:
        params["shipment_id"] = str(sid)
    if did is not None:
        params["document_id"] = str(did)
    if rid is not None:
        params["run_id"] = str(rid)
    return params


def classify_deterministic(request: QueryRequest) -> ClassificationOutcome | None:
    """Map clear Part 1 phrasings to allow-listed intents without an LLM."""
    q = request.question
    lower = q.lower()
    scoped = request.scope
    text_id = _uuid_from_text(q)

    if re.search(r"(?i)\b(summarize|summary)\b.*\b(run|verification)\b", q) or (
        "summarize_run" in lower
    ):
        run_id = scoped.run_id or text_id
        if run_id is None:
            return _unsupported(
                UnsupportedReasonCode.MISSING_SCOPE_ID,
                "summarize_run requires a run_id in scope or in the question.",
            )
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.SUMMARIZE_RUN,
                parameters={"run_id": str(run_id)},
                confidence=0.92,
            )
        )

    if re.search(
        r"(?i)(which|list|show).*(shipment).*(human.?review|auto.?approv|amendment)",
        q,
    ) or re.search(r"(?i)shipments?\s+(waiting|in)\s+(on\s+)?human", q):
        decision = _decision_from_text(q) or "HUMAN_REVIEW"
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.LIST_SHIPMENTS_BY_DECISION,
                parameters={"decision": decision},
                confidence=0.9,
            )
        )

    if re.search(r"(?i)(list|which|show).*(documents?).*(shipment|for)", q) or re.search(
        r"(?i)documents?\s+for\s+shipment",
        q,
    ):
        shipment_id = scoped.shipment_id or text_id
        if shipment_id is None:
            return _unsupported(
                UnsupportedReasonCode.MISSING_SCOPE_ID,
                "list_documents_for_shipment requires a shipment_id.",
            )
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.LIST_DOCUMENTS_FOR_SHIPMENT,
                parameters=_merge_scope(scoped, shipment_id=shipment_id),
                confidence=0.9,
            )
        )

    if re.search(r"(?i)(validation|mismatch|uncertain).*(status|result|failure|check)", q) or (
        re.search(r"(?i)\bvalidation\b", q) and (scoped.document_id or text_id)
    ):
        document_id = scoped.document_id or text_id
        if document_id is None:
            return _unsupported(
                UnsupportedReasonCode.MISSING_SCOPE_ID,
                "get_document_validation requires a document_id.",
            )
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.GET_DOCUMENT_VALIDATION,
                parameters=_merge_scope(scoped, document_id=document_id),
                confidence=0.88,
            )
        )

    if re.search(r"(?i)\b(decision|disposition|router)\b", q) and (
        scoped.document_id or text_id or "decision" in lower
    ):
        document_id = scoped.document_id or text_id
        if document_id is None and scoped.shipment_id is None:
            # list by decision already handled; require document for get_document_decision
            if _decision_from_text(q):
                return ClassificationOutcome(
                    intent=InterpretedIntent(
                        name=QueryIntentName.LIST_SHIPMENTS_BY_DECISION,
                        parameters={"decision": _decision_from_text(q)},
                        confidence=0.85,
                    )
                )
            return _unsupported(
                UnsupportedReasonCode.MISSING_SCOPE_ID,
                "get_document_decision requires a document_id.",
            )
        if document_id is not None:
            return ClassificationOutcome(
                intent=InterpretedIntent(
                    name=QueryIntentName.GET_DOCUMENT_DECISION,
                    parameters=_merge_scope(scoped, document_id=document_id),
                    confidence=0.88,
                )
            )

    if re.search(r"(?i)\b(get|show|fetch|what is|status of)\b.*\bshipment\b", q) or (
        re.search(r"(?i)^shipment\b", q) and (scoped.shipment_id or text_id)
    ):
        shipment_id = scoped.shipment_id or text_id
        if shipment_id is None:
            return _unsupported(
                UnsupportedReasonCode.MISSING_SCOPE_ID,
                "get_shipment requires a shipment_id.",
            )
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.GET_SHIPMENT,
                parameters=_merge_scope(scoped, shipment_id=shipment_id),
                confidence=0.9,
            )
        )

    if re.search(r"(?i)\b(get|show|fetch|what is|status of)\b.*\bdocument\b", q) or (
        re.search(r"(?i)^document\b", q) and (scoped.document_id or text_id)
    ):
        document_id = scoped.document_id or text_id
        if document_id is None:
            return _unsupported(
                UnsupportedReasonCode.MISSING_SCOPE_ID,
                "get_document requires a document_id.",
            )
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.GET_DOCUMENT,
                parameters=_merge_scope(scoped, document_id=document_id),
                confidence=0.9,
            )
        )

    return None


_SYSTEM_PROMPT = """You classify Nova operator questions into exactly one allow-listed intent.
Return JSON only: {"name": "<intent>", "parameters": {...}, "confidence": 0.0-1.0}
Allowed name values:
get_shipment, get_document, get_document_validation, get_document_decision,
list_shipments_by_decision, list_documents_for_shipment, summarize_run
If none apply, return {"name":"unsupported","parameters":{},"confidence":0.0}
Never invent SQL. Never invent entity IDs. Use only IDs present in the user message or scope."""


def classify_with_llm(
    request: QueryRequest,
    llm: LLMPort,
    *,
    timeout_ms: int = 5_000,
) -> ClassificationOutcome:
    scope_payload = request.scope.model_dump(mode="json")
    user_prompt = json.dumps(
        {
            "question": request.question,
            "scope": scope_payload,
            "customer_id": str(request.customer_id),
        }
    )
    try:
        response = llm.complete(
            LLMRequest(
                system_prompt=_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_format="json",
                timeout_ms=timeout_ms,
                prompt_id="query.intent.v1",
                prompt_version="1",
                response_schema_name="QueryIntent",
                temperature=0.0,
                max_tokens=256,
            )
        )
    except LLMTimeoutError as exc:
        raise exc
    except LLMError as exc:
        raise exc

    try:
        payload = json.loads(response.content)
    except json.JSONDecodeError as exc:
        raise LLMOutputError("Query classifier returned non-JSON content") from exc

    if not isinstance(payload, dict):
        raise LLMOutputError("Query classifier returned non-object JSON")

    name = payload.get("name")
    if name == "unsupported" or name is None:
        return _unsupported(
            UnsupportedReasonCode.INTENT_NOT_SUPPORTED,
            "The question could not be mapped to a supported Part 1 query intent.",
        )

    try:
        intent_name = QueryIntentName(str(name))
    except ValueError:
        return _unsupported(
            UnsupportedReasonCode.INTENT_NOT_SUPPORTED,
            "The classifier proposed an intent outside the Part 1 allow-list.",
        )

    confidence_raw = payload.get("confidence", 0.0)
    try:
        confidence = float(confidence_raw)
    except (TypeError, ValueError):
        confidence = 0.0
    if confidence < _MIN_LLM_CONFIDENCE:
        return _unsupported(
            UnsupportedReasonCode.LOW_CONFIDENCE,
            "Intent confidence was too low to execute safely.",
        )

    parameters = payload.get("parameters") or {}
    if not isinstance(parameters, dict):
        raise LLMOutputError("Query classifier parameters must be an object")

    # Drop any non-allowlisted parameter keys; never accept SQL-ish values.
    cleaned: dict[str, Any] = {}
    for key, value in parameters.items():
        if key not in {
            "shipment_id",
            "document_id",
            "run_id",
            "decision",
            "validation_id",
            "decision_id",
        }:
            continue
        if isinstance(value, str) and _SQL_INJECTION.search(value):
            return _unsupported(
                UnsupportedReasonCode.SECURITY_REJECTED,
                "Classifier parameters contained disallowed content.",
            )
        cleaned[key] = value

    # Prefer explicit request scope over model-invented IDs when scope is set.
    merged = _merge_scope(request.scope)
    merged.update({k: str(v) for k, v in cleaned.items() if v is not None})
    if intent_name == QueryIntentName.LIST_SHIPMENTS_BY_DECISION:
        decision = cleaned.get("decision") or _decision_from_text(request.question)
        if decision not in _DECISION_VALUES:
            return _unsupported(
                UnsupportedReasonCode.AMBIGUOUS_INTENT,
                "list_shipments_by_decision requires a known decision disposition.",
            )
        merged = {"decision": decision}

    return ClassificationOutcome(
        intent=InterpretedIntent(
            name=intent_name,
            parameters=merged,
            confidence=confidence,
        )
    )


def classify_intent(
    request: QueryRequest,
    llm: LLMPort | None = None,
) -> ClassificationOutcome:
    rejected = security_reject(request.question)
    if rejected is not None:
        return rejected

    deterministic = classify_deterministic(request)
    if deterministic is not None:
        return deterministic

    if llm is None:
        return _unsupported(
            UnsupportedReasonCode.INTENT_NOT_SUPPORTED,
            "Nova cannot answer this question with the Part 1 allow-listed intents.",
        )

    return classify_with_llm(request, llm)
