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
_AGREEMENT_VALUES = {
    "STRONG_AGREEMENT",
    "PARTIAL_AGREEMENT",
    "WEAK_AGREEMENT",
}

_SUGGESTIONS = [
    "Ask how many documents or shipments there are",
    "Ask to show recent documents",
    "Ask how many strong or weak agreement documents there are",
    "Ask to show documents with confidence below 70%",
    "Ask which documents have mismatches or uncertain validation",
    "Ask what fields mismatched in a named invoice",
    "Ask how many documents need human review or were auto-approved",
    "Ask why a named invoice was sent for review",
    "Ask which shipments are flagged this week",
]

# Words that precede "invoice"/"document" without naming one.
_REF_STOPWORDS = frozenset(
    {
        "a",
        "all",
        "an",
        "agreement",
        "any",
        "each",
        "every",
        "first",
        "high",
        "how",
        "last",
        "latest",
        "list",
        "low",
        "many",
        "more",
        "most",
        "new",
        "partial",
        "recent",
        "show",
        "some",
        "strong",
        "that",
        "the",
        "these",
        "this",
        "those",
        "total",
        "weak",
        "what",
        "which",
    }
)

_INVOICE_TOKEN = re.compile(r"(?i)\b(INV[-_][A-Z0-9?_\-]+)\b")
_NAMED_DOCUMENT = re.compile(r"(?i)\b(?:the\s+)?([a-z][a-z0-9]{2,})\s+(?:invoice|document|doc)\b")
_PERCENT_BELOW = re.compile(
    r"(?i)\b(?:below|under|less\s+than|lower\s+than|beneath)\s+(\d{1,3})\s*%"
)


def _document_ref_from_text(question: str) -> str | None:
    """Extract a human document reference (invoice number or qualifier word).

    Returns a token to be matched against persisted invoice numbers; it is never
    interpolated into SQL.
    """
    token = _INVOICE_TOKEN.search(question)
    if token:
        return token.group(1)
    named = _NAMED_DOCUMENT.search(question)
    if named:
        word = named.group(1).lower()
        if word not in _REF_STOPWORDS:
            return word
    return None


def _confidence_threshold_from_text(question: str) -> float | None:
    match = _PERCENT_BELOW.search(question)
    if not match:
        return None
    value = int(match.group(1))
    if value <= 0 or value > 100:
        return None
    return value / 100.0


def _document_scope_params(
    question: str,
    scope: QueryScope,
    text_id: UUID | None,
) -> dict[str, Any] | None:
    """Resolve a document target from scope, an explicit UUID, or a name."""
    document_id = scope.document_id or text_id
    if document_id is not None:
        return {"document_id": str(document_id)}
    reference = _document_ref_from_text(question)
    if reference is not None:
        return {"document_ref": reference}
    return None


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
    if re.search(
        r"(?i)human\s+review|waiting\s+on\s+(human\s+)?review|flagged|"
        r"need(s|ing|ed)?\s+(a\s+)?review|sent\s+(to|for)\s+review|for\s+review",
        question,
    ):
        return "HUMAN_REVIEW"
    if re.search(r"(?i)auto[_\s-]?approv|\bapprov(ed|al)\b", question):
        return "AUTO_APPROVE"
    if re.search(r"(?i)amendment|\bamend\w*\b|\brejected\b", question):
        return "AMENDMENT_REQUEST"
    return None


def _time_range_from_text(question: str) -> dict[str, str] | None:
    week = r"(?i)\b(this\s+week|past\s+week|last\s+7\s+days|last\s+seven\s+days)\b"
    if re.search(week, question):
        return {"preset": "this_week"}
    today = r"(?i)\b(today|this\s+day)\b"
    if re.search(today, question):
        return {"preset": "today"}
    month = r"(?i)\b(this\s+month|past\s+month|last\s+30\s+days)\b"
    if re.search(month, question):
        return {"preset": "this_month"}
    return None


def _agreement_from_text(question: str) -> str | None:
    """Detect an agreement category, including superlatives and bare adjectives.

    Accepts "strong agreement", "strongest agreement documents", and plain
    "weak documents". Confidence phrasings are handled separately and must not
    reach here.
    """
    # "<adjective> agreement|documents|docs"
    qualified = r"[\s-]+(agreement|documents?|docs?)\b"
    if (
        re.search(rf"(?i)\b(strong(est)?|highest){qualified}", question)
        or re.search(r"(?i)\bstrongly\s+agree", question)
        or re.search(r"(?i)\bhigh\s+agreement\b", question)
    ):
        return "STRONG_AGREEMENT"
    if re.search(rf"(?i)\bpartial(ly)?{qualified}", question) or re.search(
        r"(?i)\bpartially\s+agree",
        question,
    ):
        return "PARTIAL_AGREEMENT"
    if (
        re.search(rf"(?i)\b(weak(est)?|lowest){qualified}", question)
        or re.search(r"(?i)\bweakly\s+agree", question)
        or re.search(r"(?i)\blow\s+agreement\b", question)
    ):
        return "WEAK_AGREEMENT"
    upper = question.upper()
    for value in _AGREEMENT_VALUES:
        if value in upper:
            return value
    return None


def _resolve_time_range(question: str, scope: QueryScope) -> dict[str, Any] | None:
    time_range = _time_range_from_text(question)
    if time_range is None and isinstance(scope.time_range, dict):
        time_range = dict(scope.time_range)
    return time_range


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

    # Agreement / attention / decision / mismatch counts (document-level analytics).
    if re.search(
        r"(?i)\b(require[s]?\s+attention|needs?\s+attention|requiring\s+attention)\b",
        q,
    ):
        parameters: dict[str, Any] = {}
        time_range = _resolve_time_range(q, scoped)
        if time_range is not None:
            parameters["time_range"] = time_range
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.COUNT_DOCUMENTS_REQUIRING_ATTENTION,
                parameters=parameters,
                confidence=0.92,
            )
        )

    def with_window(base: dict[str, Any]) -> dict[str, Any]:
        time_range = _resolve_time_range(q, scoped)
        if time_range is not None:
            base["time_range"] = time_range
        return base

    counting = re.search(r"(?i)\b(how many|count|number of)\b", q) is not None
    listing = re.search(r"(?i)\b(which|show|list|display|give me)\b", q) is not None

    # "Why was X sent for review?" / "What went wrong with X?" -> decision reasoning.
    if re.search(
        r"(?i)\bwhy\b.*\b(review|routed|rejected|flagged|amendment|approved|sent)\b",
        q,
    ) or re.search(r"(?i)\b(went\s+wrong|what\s+happened|what'?s\s+wrong)\b", q):
        target = _document_scope_params(q, scoped, text_id)
        if target is None:
            return _unsupported(
                UnsupportedReasonCode.MISSING_SCOPE_ID,
                "Explaining a routing decision requires a document id or invoice reference.",
            )
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.EXPLAIN_DOCUMENT_REVIEW,
                parameters=target,
                confidence=0.92,
            )
        )

    # "Which fields mismatched / failed?" -> field-level validation for one document.
    if re.search(r"(?i)\b(what|which)\s+fields?\b", q) and re.search(
        r"(?i)\b(mismatch\w*|fail\w*|wrong|invalid|error\w*|disagree\w*)\b",
        q,
    ):
        target = _document_scope_params(q, scoped, text_id)
        if target is None:
            return _unsupported(
                UnsupportedReasonCode.MISSING_SCOPE_ID,
                "Listing mismatched fields requires a document id or invoice reference.",
            )
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.GET_DOCUMENT_MISMATCHED_FIELDS,
                parameters=target,
                confidence=0.92,
            )
        )

    # Validation questions: count or list — kept distinct.
    if re.search(r"(?i)\bmismatch(es|ed)?\b", q):
        if counting:
            return ClassificationOutcome(
                intent=InterpretedIntent(
                    name=QueryIntentName.COUNT_DOCUMENTS_WITH_MISMATCHES,
                    parameters=with_window({}),
                    confidence=0.9,
                )
            )
        if listing or re.search(r"(?i)\bdocuments?\s+have\s+mismatches?\b", q):
            return ClassificationOutcome(
                intent=InterpretedIntent(
                    name=QueryIntentName.LIST_DOCUMENTS_WITH_MISMATCHES,
                    parameters=with_window({}),
                    confidence=0.9,
                )
            )

    if re.search(r"(?i)\buncertain\b", q) and (counting or listing):
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.LIST_DOCUMENTS_WITH_UNCERTAIN_VALIDATION,
                parameters=with_window({}),
                confidence=0.9,
            )
        )

    # Confidence questions are distinct from agreement classification.
    if re.search(r"(?i)\bconfidence\b", q) and not re.search(r"(?i)\bagreement\b", q):
        if re.search(r"(?i)\b(lowest|worst|least)\b", q):
            return ClassificationOutcome(
                intent=InterpretedIntent(
                    name=QueryIntentName.LIST_DOCUMENTS_BY_CONFIDENCE,
                    parameters={"order": "lowest"},
                    confidence=0.92,
                )
            )
        threshold = _confidence_threshold_from_text(q)
        if threshold is not None or re.search(r"(?i)\blow([\s-]|\b)", q):
            parameters = {"max_confidence": threshold if threshold is not None else 0.70}
            return ClassificationOutcome(
                intent=InterpretedIntent(
                    name=QueryIntentName.LIST_DOCUMENTS_BY_CONFIDENCE,
                    parameters=with_window(parameters),
                    confidence=0.9,
                )
            )

    if re.search(r"(?i)\b(compare|breakdown|distribution|versus|vs\.?)\b", q) and re.search(
        r"(?i)\b(agreement|strong|weak|confidence)\b",
        q,
    ):
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.COMPARE_AGREEMENT,
                parameters=with_window({}),
                confidence=0.9,
            )
        )

    agreement = _agreement_from_text(q)
    if agreement is not None and re.search(
        r"(?i)\b(show|list|which|display)\b",
        q,
    ):
        parameters = {"agreement": agreement}
        time_range = _resolve_time_range(q, scoped)
        if time_range is not None:
            parameters["time_range"] = time_range
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.LIST_DOCUMENTS_BY_AGREEMENT,
                parameters=parameters,
                confidence=0.92,
            )
        )

    if agreement is not None and re.search(
        r"(?i)\b(documents?\s+with\s+(strong|partial|weak)\s+agreement)\b",
        q,
    ):
        parameters = {"agreement": agreement}
        time_range = _resolve_time_range(q, scoped)
        if time_range is not None:
            parameters["time_range"] = time_range
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.LIST_DOCUMENTS_BY_AGREEMENT,
                parameters=parameters,
                confidence=0.9,
            )
        )

    if agreement is not None and re.search(
        r"(?i)\b(how many|count|number of)\b",
        q,
    ):
        parameters = {"agreement": agreement}
        time_range = _resolve_time_range(q, scoped)
        if time_range is not None:
            parameters["time_range"] = time_range
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.COUNT_DOCUMENTS_BY_AGREEMENT,
                parameters=parameters,
                confidence=0.92,
            )
        )

    # Any counting question that names a disposition, with or without a noun
    # ("how many were flagged?", "how many need review?").
    if counting and not re.search(r"(?i)\bshipments?\b", q):
        decision = _decision_from_text(q)
        if decision is not None:
            parameters = {"decision": decision}
            time_range = _resolve_time_range(q, scoped)
            if time_range is not None:
                parameters["time_range"] = time_range
            return ClassificationOutcome(
                intent=InterpretedIntent(
                    name=QueryIntentName.COUNT_DOCUMENTS_BY_DECISION,
                    parameters=parameters,
                    confidence=0.9,
                )
            )

    # Documents routed to a disposition (distinct from shipment-level listing).
    if listing and re.search(r"(?i)\bdocuments?\b", q):
        decision = _decision_from_text(q)
        if decision is not None and re.search(
            r"(?i)\b(human\s+review|auto[_\s-]?approv\w*|amendment|routed|need[s]?\s+review)\b",
            q,
        ):
            return ClassificationOutcome(
                intent=InterpretedIntent(
                    name=QueryIntentName.LIST_DOCUMENTS_BY_DECISION,
                    parameters=with_window({"decision": decision}),
                    confidence=0.9,
                )
            )

    if listing and re.search(r"(?i)\b(recent|latest|newest)\b.*\bdocuments?\b", q):
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.LIST_RECENT_DOCUMENTS,
                parameters=with_window({}),
                confidence=0.9,
            )
        )

    # Plain totals. These run after the specific analytics rules above so that
    # "how many documents have mismatches" is never answered as a bare total.
    # A disposition word means the caller wants the decision-scoped intents below.
    plain_total = _decision_from_text(q) is None

    if counting and plain_total and re.search(r"(?i)\bshipments?\b", q):
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.COUNT_SHIPMENTS,
                parameters=with_window({}),
                confidence=0.9,
            )
        )

    if counting and re.search(r"(?i)\bdocuments?\b", q):
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.COUNT_DOCUMENTS,
                parameters=with_window({}),
                confidence=0.9,
            )
        )

    if (
        listing
        and plain_total
        and re.search(r"(?i)\bshipments?\b", q)
        and scoped.shipment_id is None
        and text_id is None
    ):
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.LIST_SHIPMENTS,
                parameters=with_window({}),
                confidence=0.88,
            )
        )

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

    # Shipment questions that name a disposition (count or list).
    if (
        re.search(r"(?i)\bshipments?\b", q) and _decision_from_text(q) is not None
    ) or re.search(r"(?i)(shipments?\s+(waiting|in|flagged)|flagged\s+(this\s+)?week)", q):
        decision = _decision_from_text(q) or "HUMAN_REVIEW"
        parameters = {"decision": decision}
        time_range = _resolve_time_range(q, scoped)
        if time_range is not None:
            parameters["time_range"] = time_range
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.LIST_SHIPMENTS_BY_DECISION,
                parameters=parameters,
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
        re.search(r"(?i)\bvalidation\b", q)
        and (scoped.document_id or text_id or _document_ref_from_text(q))
    ):
        target = _document_scope_params(q, scoped, text_id)
        if target is None:
            return _unsupported(
                UnsupportedReasonCode.MISSING_SCOPE_ID,
                "get_document_validation requires a document id or invoice reference.",
            )
        return ClassificationOutcome(
            intent=InterpretedIntent(
                name=QueryIntentName.GET_DOCUMENT_VALIDATION,
                parameters=target,
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
list_shipments_by_decision, list_documents_for_shipment, summarize_run,
count_documents_by_agreement, list_documents_by_agreement,
count_documents_requiring_attention, count_documents_by_decision,
count_documents_with_mismatches, count_documents, count_shipments,
list_shipments, list_recent_documents, list_documents_by_decision,
list_documents_by_confidence, list_documents_with_mismatches,
list_documents_with_uncertain_validation, get_document_mismatched_fields,
explain_document_review, compare_agreement
If none apply, return {"name":"unsupported","parameters":{},"confidence":0.0}
Never invent SQL. Never invent entity IDs. Use only IDs present in the user message or scope.
Distinguish the concepts: "confidence" is a numeric score
(list_documents_by_confidence), "agreement" is a classification
(count/list_documents_by_agreement), "mismatch"/"uncertain" are validation
outcomes (list_documents_with_mismatches / _with_uncertain_validation), and
"human review"/"auto approve"/"amendment" are router decisions
(count/list_documents_by_decision). Do not collapse them into one intent.
Agreement values: STRONG_AGREEMENT, PARTIAL_AGREEMENT, WEAK_AGREEMENT.
Decision values: AUTO_APPROVE, HUMAN_REVIEW, AMENDMENT_REQUEST.
Parameters may include: shipment_id, document_id, run_id, document_ref,
decision, agreement, max_confidence (0-1), order ("lowest"), time_range."""


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
            "agreement",
            "time_range",
            "document_ref",
            "max_confidence",
            "order",
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
    merged.update({k: str(v) for k, v in cleaned.items() if v is not None and k != "time_range"})
    if "time_range" in cleaned and isinstance(cleaned["time_range"], dict):
        merged["time_range"] = cleaned["time_range"]
    elif _resolve_time_range(request.question, request.scope) is not None:
        merged["time_range"] = _resolve_time_range(request.question, request.scope)

    if intent_name == QueryIntentName.LIST_SHIPMENTS_BY_DECISION:
        decision = cleaned.get("decision") or _decision_from_text(request.question)
        if decision not in _DECISION_VALUES:
            return _unsupported(
                UnsupportedReasonCode.AMBIGUOUS_INTENT,
                "list_shipments_by_decision requires a known decision disposition.",
            )
        merged = {"decision": decision}
        if "time_range" in cleaned and isinstance(cleaned["time_range"], dict):
            merged["time_range"] = cleaned["time_range"]

    if intent_name in {
        QueryIntentName.COUNT_DOCUMENTS_BY_AGREEMENT,
        QueryIntentName.LIST_DOCUMENTS_BY_AGREEMENT,
    }:
        agreement = cleaned.get("agreement") or _agreement_from_text(request.question)
        if agreement not in _AGREEMENT_VALUES:
            return _unsupported(
                UnsupportedReasonCode.AMBIGUOUS_INTENT,
                "agreement intents require STRONG_AGREEMENT, PARTIAL_AGREEMENT, or WEAK_AGREEMENT.",
            )
        merged = {"agreement": agreement}
        if "time_range" in cleaned and isinstance(cleaned["time_range"], dict):
            merged["time_range"] = cleaned["time_range"]

    if intent_name == QueryIntentName.COUNT_DOCUMENTS_BY_DECISION:
        decision = cleaned.get("decision") or _decision_from_text(request.question)
        if decision not in _DECISION_VALUES:
            return _unsupported(
                UnsupportedReasonCode.AMBIGUOUS_INTENT,
                "count_documents_by_decision requires a known decision disposition.",
            )
        merged = {"decision": decision}
        if "time_range" in cleaned and isinstance(cleaned["time_range"], dict):
            merged["time_range"] = cleaned["time_range"]

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
