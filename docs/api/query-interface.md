# Natural-language query interface

Contract and implementation status for `POST /v1/query` — grounded Q&A over **persisted** Nova verification data (`REQ-QUERY-002`, `REQ-QUERY-003`).

**Status:** Phase 8 implemented (`src/nova/query/`, `POST /v1/query`).

## Security requirement (normative)

**Natural-language query must not execute arbitrary LLM-generated SQL (or shell, or ORM code) against the database.**

Allowed execution path:

```text
user question
  → security gate (reject SQL / prompt abuse / schema discovery)
  → intent interpretation (deterministic + optional constrained LLM classify)
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
    "run_id": null,
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
| `options.max_results` | no | Server clamps to a safe maximum (50) |

## Response envelope

See contracts in `src/nova/contracts/query.py`. `status` ∈ `RESULT` | `EMPTY` | `UNSUPPORTED` | `FAILURE`.

HTTP mapping:

| Query `status` | HTTP |
|----------------|------|
| `RESULT` / `EMPTY` / `UNSUPPORTED` / `FAILURE` | **200** (valid request body) |
| Auth problems | **401** / **403** |
| Malformed body | **400** / **422** |

## Part 1 allow-listed intents

| Intent `name` | Purpose | Required parameters |
|---------------|---------|---------------------|
| `get_shipment` | Fetch shipment by id | `shipment_id` |
| `get_document` | Fetch document + status by id | `document_id` |
| `get_document_validation` | Validation outcome + failing checks | `document_id` |
| `get_document_decision` | Router decision for a document | `document_id` |
| `list_shipments_by_decision` | Filter by disposition | `decision` ∈ AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST |
| `list_documents_for_shipment` | 1:N documents listing | `shipment_id` |
| `summarize_run` | Extraction/validation/decision summary for a run | `run_id` |

Adding intents requires documentation + tests; the LLM may **classify** among this set, not invent new executable intents at runtime.

## Query flow (implementation)

1. Authenticate API key.
2. Validate `QueryRequest` (Pydantic).
3. `QueryService.answer`:
   - Security gate rejects SQL injection, arbitrary SQL requests, schema discovery, prompt injection, and mutating commands.
   - Deterministic classifier maps clear phrasings to intents.
   - Optional LLM classify (`query.intent.v1`) only among allow-listed names; invented names → `UNSUPPORTED`.
   - `QueryRepository` executes parameterized SQLAlchemy reads scoped by `customer_id`.
   - `answer_summary` is built only from returned rows (or an explicit emptiness statement).

## LLM boundary

| Allowed | Forbidden |
|---------|-----------|
| Classify intent among allow-list | Execute SQL |
| Suggest parameter keys from question/scope | Bypass customer scoping |
| Return low-confidence → UNSUPPORTED | Invent shipment/document/field/decision values |
| | Override persisted validation or decisions |

Default MockLLM for query returns `{name: unsupported}` so unknown questions do not fabricate answers.

## Data grounding

Responses cite persisted IDs where appropriate: `shipment_id`, `document_id`, `validation_id`, `decision_id`, `run_id`, validation `reason_code`, decision disposition, timestamps.

Do not expose connection strings, stack traces, or unrelated schema catalogs.

## Failure behavior

| Condition | `status` | Notes |
|-----------|----------|-------|
| Supported intent, rows found | `RESULT` | Grounded records + citations |
| Supported intent, no rows / missing entity | `EMPTY` | Honest summary; no invented rows |
| Outside allow-list / security reject | `UNSUPPORTED` | Structured reason + suggestions |
| LLM timeout / provider / malformed JSON | `FAILURE` | `AI_PROVIDER_*`, retryable when transient |
| Database error | `FAILURE` | `DATABASE_ERROR`, retryable |

## Limitations (Part 1)

- No free-form BI / analytics / joins invented at runtime
- No mutating commands via NL
- No cross-customer analytics
- Time-range filters in `scope` are accepted in the contract but not yet applied as SQL filters
- Full pipeline orchestration that *writes* validation/decision rows is Phase 7; Phase 8 reads whatever is persisted (tests seed SoR rows)

## Part 2 extension points

- Additional allow-listed intents (cross-document, approval queue, outbound draft status)
- Stronger RBAC beyond customer_id + API key
- Optional search document / `tsvector` index — still not LLM SQL
- Human-approval actions remain separate write APIs, never NL mutate

## Observability

Log: `trace_id`, `customer_id`, intent `name`, `status`, latency (no raw document bodies, no secrets).

## Related

- Feature: [../features/query-intelligence-api.md](../features/query-intelligence-api.md)
- [contracts.md](./contracts.md)
- [error-model.md](./error-model.md)
- Requirements: `REQ-QUERY-001`–`003`
- Security: `docs/security/baseline.md`, `docs/security/query-api.md`
- Tests: `tests/query/`
