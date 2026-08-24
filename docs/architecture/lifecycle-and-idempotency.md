# Lifecycle, state, and idempotency

API-oriented idempotency detail: [`docs/api/idempotency.md`](../api/idempotency.md).

## Lifecycles (summary)

| Entity | States (Part 1+) |
|--------|------------------|
| Shipment | DRAFT → OPEN → UNDER_REVIEW / NEEDS_AMENDMENT / APPROVED → CLOSED |
| Document | RECEIVED → PROCESSING → PROCESSED / FAILED; SUPERSEDED on new version |
| Validation | PENDING → RUNNING → COMPLETED / FAILED |
| Decision | PENDING → DECIDED; Part 2 adds approval transitions |

`DocumentVersion` is immutable. Reprocessing creates new runs; prior rows remain for audit. Decisions are append-only (`supersedes_decision_id`).

## Duplicate handling

- Content SHA-256 on ingest
- `Idempotency-Key` on ingest/reprocess
- Same key replay returns prior result (`409` on conflicting body)

## Retry

- LLM transient: max N (default 2) with backoff
- Schema: optional 1 repair
- Non-retryable: client validation, auth

## Partial failure & resume

Extraction `PARTIAL` still enters validation; AUTO_APPROVE unlikely. Orchestrator checkpoints stages and resumes from first incomplete stage unless forced reprocess.

## Authority

Persistence lifecycle enums in [`../database/domain-model.md`](../database/domain-model.md) are authoritative. Values in this document are illustrative projections for API/UI.
