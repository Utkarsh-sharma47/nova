# Contract alignment (Phase 2)

Normative mapping across agent semantics, Pydantic runtime schemas, HTTP API, and PostgreSQL persistence.

## Sources of truth

| Concern | Authority |
|---------|-----------|
| Agent safety semantics (presence, uncertainty → disposition) | [`docs/agents/contracts.md`](../agents/contracts.md), [`docs/agents/trust-model.md`](../agents/trust-model.md), [ADR-0010](../decisions/0010-ai-agent-contracts-and-trust-model.md) |
| Runtime schema encoding | `src/nova/contracts/` (Pydantic) — must enforce agent invariants |
| HTTP wire contracts | [`docs/api/contracts.md`](../api/contracts.md) |
| Persistence shape | [`docs/database/domain-model.md`](../database/domain-model.md), [`schema-design.md`](../database/schema-design.md) |

If documents disagree, **agent semantics win for safety**; Pydantic and API docs must be updated to match. Persistence may rename columns but must preserve meaning.

## Identity mapping

| Concept | Agents / API | Pydantic | Database |
|---------|--------------|----------|----------|
| Verification run | `run_id` | `run_id` (+ `trace_id` for logs) | `verification_runs.verification_run_id` |
| Observability correlation | `trace_id` | `trace_id` | `audit_events.correlation_id` (store trace_id) |
| Document | `document_id` | `document_id` | `documents.document_id` |
| Document version | `document_version_id` | `document_version_id` | `document_versions.document_version_id` |
| Extracted field key | `name` | `field_name` | `extracted_fields.field_key` |

Part 1 demos may set `trace_id == run_id`. Production should keep them distinct when an HTTP request fans out to multiple runs.

## Presence and uncertainty

| Agent | Pydantic | DB |
|-------|----------|-----|
| `FieldPresence` KNOWN/UNKNOWN/MISSING/AMBIGUOUS | `ExtractedField.presence` | `is_missing` + `absence_reason` derived from presence |
| `UncertaintyFlag` | `ExtractedField.uncertainty` | optional JSON alongside evidence |
| confidence `[0,1]\|null` | `confidence` | `confidence` |

**Invariant (enforced in Pydantic):** `presence != KNOWN ⇒ value is null`; `presence == KNOWN ⇒ value non-null and evidence non-empty`.

## Extraction status

Canonical wire value: **`SUCCEEDED`**. `COMPLETED` is accepted as an input alias and normalized to `SUCCEEDED`.

## Validation check naming

| Agent / API narrative | Pydantic | DB |
|-----------------------|----------|-----|
| `result` | `outcome` | check result column |
| `deterministic` | `deterministic` | `check_kind` / flag |
| evidence[] | `evidence` | `evidence_json` |

## Decision / error envelopes

- Stage `DecisionResult.decision` uses `AUTO_APPROVE` \| `HUMAN_REVIEW` \| `AMENDMENT_REQUEST`.
- HTTP errors use nested `{ "error": { "code", "message", "details", "trace_id", "retryable" } }` ([error-model.md](../api/error-model.md)).
- Application `ErrorResponse` carries `error_type`, `error_code`, `message`, `trace_id`, `retryable` for internal mapping into the HTTP envelope.
- AI provider transient failures map to HTTP **502** with `retryable=true` when safe (API normative). Architecture logical `AIProviderError` → 502 for Part 1 (not 503).

## API paths and idempotency

- Resource base path: **`/v1`** (not `/api/v1`).
- Ingestion: **`POST /v1/documents`** → **202 Accepted**; **`Idempotency-Key` required**.

## Lifecycle enums

Domain model enums in [`docs/database/domain-model.md`](../database/domain-model.md) are authoritative for persistence. API document processing status (`ACCEPTED`…`DECIDED`) is a **projection** for clients, not a second lifecycle SoT.

## Timeouts (defaults)

| Stage | `timeout_ms` default |
|-------|----------------------|
| Extractor | 60000 |
| Validator | 30000 |
| Router | 15000 |

Bounded retries remain policy in agent docs (max 2); not infinite loops.
