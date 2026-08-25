# Natural-language query interface

Contract for `POST /v1/query` — grounded Q&A over **persisted** Nova verification data (`REQ-QUERY-002`, `REQ-QUERY-003`).

**Status:** Implemented (Phase 8+; adapted to Phase 7 persistence schema).

## Security requirement (normative)

**Natural-language query must not execute arbitrary LLM-generated SQL (or shell, or ORM code) against the database.**

Allowed execution path:

```text
user question
  → intent interpretation (constrained)
  → allow-listed query plan / parameterized repository calls
  → read persisted records
  → grounded answer or explicit unsupported/failure
```

Forbidden:

- Sending model-produced SQL strings to the database driver
- `eval` of model-produced code
- Unconstrained tool use that can mutate state

This is a **security and correctness** requirement, not an optimization hint. Violating it is an architecture defect.

## Distinctions the API must preserve

Every response must make these concepts separately visible (not collapsed into a single free-text blob):

| Concept | Meaning |
|---------|---------|
| **User question** | Exact string the caller submitted |
| **Interpreted intent** | Structured, allow-listed intent the system believes was asked |
| **Query result** | Grounded answer payload when the intent is supported and data exists |
| **Unsupported query** | Intent outside the allow-list or not safely executable |
| **Failure** | System/dependency error while interpreting or retrieving |

## Request

`POST /v1/query`

```json
{
  "question": "Which shipments are waiting on human review?",
  "customer_id": "cust_…",
  "scope": {
    "shipment_id": null,
    "document_id": null,
    "time_range": null
  },
  "options": {
    "max_results": 20
  }
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `question` | yes | 1–2000 characters; plain text |
| `customer_id` | yes (Part 1) | Scopes reads; prevents cross-customer leakage |
| `scope` | no | Optional filters; cannot expand beyond caller auth |
| `options.max_results` | no | Server clamps to a safe maximum |

## Response envelope

```json
{
  "question": "Which shipments are waiting on human review?",
  "interpreted_intent": {
    "name": "list_shipments_by_decision",
    "version": "1",
    "parameters": {
      "decision": "HUMAN_REVIEW"
    },
    "confidence": 0.81
  },
  "status": "RESULT",
  "result": {
    "answer_summary": "2 shipments are in HUMAN_REVIEW.",
    "records": [
      {
        "type": "shipment",
        "shipment_id": "shp_…",
        "decision": "HUMAN_REVIEW",
        "document_ids": ["doc_…"]
      }
    ],
    "citations": [
      {
        "type": "decision",
        "id": "dec_…",
        "shipment_id": "shp_…"
      }
    ]
  },
  "unsupported": null,
  "failure": null,
  "trace_id": "01J9…"
}
```

### `status` enum

| Value | When | Populated fields |
|-------|------|------------------|
| `RESULT` | Supported intent; answer grounded in persisted rows | `result` set; `unsupported`/`failure` null |
| `UNSUPPORTED` | Cannot safely map to allow-listed intent/plan | `unsupported` set |
| `FAILURE` | Interpreter or datastore error | `failure` set |
| `EMPTY` | Supported intent; no matching records | `result` with empty `records` and honest summary |

`EMPTY` is **not** failure and **not** an invitation to invent rows.

## Interpreted intent

```json
{
  "name": "get_document_decision",
  "version": "1",
  "parameters": { "document_id": "doc_…" },
  "confidence": 0.9
}
```

| Field | Rules |
|-------|-------|
| `name` | Must be one of the allow-listed intent names below (or `unsupported` path) |
| `parameters` | Only declared parameters for that intent; types validated server-side |
| `confidence` | Optional; low confidence should prefer `UNSUPPORTED` over guessing |

### Part 1 allow-listed intents (minimum)

| Intent `name` | Purpose |
|---------------|---------|
| `get_shipment` | Fetch shipment by id |
| `get_document` | Fetch document + status by id |
| `get_document_validation` | Validation outcome for a document |
| `get_document_decision` | Router decision for a document |
| `list_shipments_by_decision` | Filter by `AUTO_APPROVE` \| `HUMAN_REVIEW` \| `AMENDMENT_REQUEST` |
| `list_documents_for_shipment` | 1:N documents listing |
| `summarize_run` | Summarize extraction/validation/decision for a `run_id` using stored fields only |

Adding intents requires documentation + tests; the LLM may **classify** among this set, not invent new executable intents at runtime.

## Unsupported

```json
{
  "reason_code": "INTENT_NOT_SUPPORTED",
  "message": "Nova cannot answer questions that require predicting future vessel ETAs.",
  "suggestions": [
    "Ask for a shipment or document by id",
    "Ask which shipments are in HUMAN_REVIEW"
  ]
}
```

Common `reason_code` values: `INTENT_NOT_SUPPORTED`, `AMBIGUOUS_INTENT`, `OUT_OF_SCOPE`, `MISSING_SCOPE_ID`.

## Failure

Uses the same philosophy as [error-model.md](./error-model.md), embedded for this POST:

```json
{
  "code": "AI_PROVIDER_ERROR",
  "message": "Query interpretation temporarily unavailable.",
  "retryable": true
}
```

HTTP mapping:

| Query `status` | HTTP |
|----------------|------|
| `RESULT` / `EMPTY` / `UNSUPPORTED` | **200** (business outcome, not transport failure) |
| Auth problems | **401** / **403** |
| Malformed body | **400** / **422** |
| Interpreter/dependency hard failure with no body status | **502** / **503** with error envelope |

Prefer **200 + `status=FAILURE`** when the HTTP request itself was valid and the failure is domain-level; use 5xx when the service cannot form a contract-compliant body.

## Grounding rules

- `answer_summary` must be entailed by `records` / `citations` or be an explicit emptiness statement.
- If data is unknown, say so — **do not invent** field values, decisions, or counts (`REQ-QUERY-003`).
- Citations should reference persisted entity IDs (`shipment_id`, `document_id`, `validation_id`, `decision_id`, `run_id`).

## Observability

Log: `trace_id`, `customer_id`, intent `name`, `status`, latency, token/cost for interpretation (no raw document bodies).  
Metrics (later): unsupported rate, empty rate, interpreter failures, latency.

## Out of scope (Part 1)

- Mutating commands via NL (“approve this shipment”)
- Cross-customer analytics
- Free-form BI / SQL notebooks

## Related

- [contracts.md](./contracts.md) — endpoint summary
- [error-model.md](./error-model.md)
- Requirements: `REQ-QUERY-001`–`003`
- Security: `docs/security/baseline.md`; prompt-injection handling in Phase 2 security architecture
