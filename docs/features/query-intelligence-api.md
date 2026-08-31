# Feature: Query / Intelligence API

## Summary

Phase 8 implements grounded natural-language query over Nova’s system of record via `POST /v1/query`. Operators ask supported business questions; the system classifies to an allow-listed intent and answers only from parameterized PostgreSQL/SQLite reads.

## Requirements

- `REQ-QUERY-001` — query layer over persisted data
- `REQ-QUERY-002` — natural-language query over verification data
- `REQ-QUERY-003` — must not invent facts not present in persisted data
- `REQ-SEC-*` — no arbitrary SQL / prompt abuse leading to data exfiltration

## Behavior

Supported intents (Part 1 allow-list). The classifier keeps **confidence**,
**agreement**, **validation**, and **decision** as separate concepts; questions
about them do not collapse into one intent.

| Category | Intent | Example question |
|----------|--------|------------------|
| Documents | `count_documents` | How many documents are there? |
| Documents | `list_recent_documents` | Show recent documents. |
| Documents | `get_document` | What is the status of document `<uuid>`? |
| Documents | `list_documents_for_shipment` | Which documents belong to this shipment? |
| Shipments | `count_shipments` | How many shipments are there? |
| Shipments | `list_shipments` | Show shipments for this customer. |
| Shipments | `list_shipments_by_decision` | Which shipments were flagged this week? |
| Shipments | `get_shipment` | What is the status of shipment `<uuid>`? |
| Validation | `count_documents_with_mismatches` | How many documents have mismatches? |
| Validation | `list_documents_with_mismatches` | Which documents have mismatches? |
| Validation | `get_document_mismatched_fields` | What fields mismatched in the messy invoice? |
| Validation | `list_documents_with_uncertain_validation` | Which documents have uncertain validation? |
| Validation | `get_document_validation` | Show validation results for document `<uuid>`. |
| Decisions | `count_documents_by_decision` | How many documents need human review? |
| Decisions | `list_documents_by_decision` | Show documents routed to HUMAN_REVIEW. |
| Decisions | `get_document_decision` | What is the decision for document `<uuid>`? |
| Decisions | `explain_document_review` | Why was the messy invoice sent for review? |
| Confidence | `list_documents_by_confidence` | Show documents with confidence below 70% / lowest confidence. |
| Agreement | `count_documents_by_agreement` | How many strong agreement documents are there? |
| Agreement | `list_documents_by_agreement` | Show weak agreement documents. |
| Agreement | `count_documents_requiring_attention` | How many documents require attention? |
| Agreement | `compare_agreement` | Compare strong vs weak documents. |
| Runs | `summarize_run` | Summarize verification run `<uuid>`. |

### Document references

Document-scoped intents accept a `document_id` (from scope or the question) or a
`document_ref` — a fragment of the persisted invoice number, e.g. "the messy
invoice" resolves against `INV-MESSY-...`. The reference is matched in Python over
customer-scoped rows, so user text never reaches SQL.

Matching tolerates inflected words: "the rejected invoice" resolves
`INV-REJECT-9001` by comparing invoice-number tokens of at least four characters,
so a generic prefix such as `INV` cannot match everything.

If a reference matches more than one document the response is `UNSUPPORTED` with
reason `AMBIGUOUS_INTENT` and the candidate invoice numbers as suggestions. One
document is never chosen arbitrarily.

### Phrasing coverage

Disposition, agreement, and failure questions do not require a canonical noun.
"how many were flagged?", "how many need review?", "show weak documents", "show me
the strongest agreement documents", "how many shipments were approved?", and "what
went wrong with INV-REJECT-9001?" all map to distinct intents. A question that
names no document ("which fields failed?") returns `MISSING_SCOPE_ID` rather than
guessing a document.

### Time filters

`this week`, `today`, and `this month` are converted into concrete UTC boundaries
and applied as parameterized filters on the relevant timestamp column
(`documents.updated_at`, `shipments.updated_at`, or `decisions.decided_at`), not
merely detected in the text.

### Response grounding

Every `RESULT` payload carries the intent name, the parameters actually applied,
the records read from the database, citations to the underlying rows, and the note
`Source: persisted Nova document/validation/decision records.` Zero matches return
`EMPTY` with an explicit "0" answer rather than an invented example.

Unsupported / unsafe questions return structured `UNSUPPORTED`, and database
errors return `FAILURE` — never a fabricated success.

Agreement classification is derived deterministically from persisted extraction confidence
and validation outcomes. It does **not** replace Router decisions.

## Architecture

```text
API → QueryService → classifier (security + deterministic + optional LLM)
                  → QueryRepository (SQLAlchemy, customer-scoped)
                  → QueryResponse (RESULT | EMPTY | UNSUPPORTED | FAILURE)
```

Persistence tables used for reads: Phase 7 `validations` (checks embedded in
`result_json`) and `decisions` (Alembic `0003_phase6_decisions` + `0004_phase7_pipeline`).
No separate Phase 8 schema migration is required on the Phase 7 lineage.

## LLM boundary

LLM may classify intent only. Final factual values come exclusively from repository results.

## Security

See [../security/query-api.md](../security/query-api.md). Tests cover SQL injection, prompt injection, schema discovery, and invented intents.

## Testing

`tests/query/` — supported intents, security, API validation, LLM/DB failure modes. Fixtures seed deterministic SoR rows and assert returned IDs exist in the seed.

`tests/query/seed.py` provides a deterministic seven-document dataset covering
strong / partial / weak agreement, mismatch, uncertain, low confidence, missing
evidence, and all three dispositions.

`tests/query/test_query_phrasing.py` covers the natural-language phrasing
regressions above, invoice-reference resolution including inflected forms, and the
ambiguous-reference response.

`tests/query/test_query_evaluation.py` is the query evaluation suite. Each case
asserts question → intent → parameters → grounded answer, with expected counts
computed by independent SQL against the same database, so a hardcoded answer
cannot pass. It covers document/shipment counts, agreement, low confidence,
mismatches, uncertain validation, all dispositions, time ranges,
document-specific reasoning, unsupported questions, SQL injection, prompt
injection, malformed/low-confidence LLM intents, and database failure.

## Part 2

Additional intents and RBAC without opening a free-form SQL channel.

## Related

- [../api/query-interface.md](../api/query-interface.md)
- `src/nova/query/`
- `src/nova/contracts/query.py`
