# Idempotency (document ingestion)

How Nova avoids accidental duplicate processing when clients retry document ingestion (`REQ-DATA-003`, architecture principle: idempotency).

**Status:** Implemented for `POST /v1/documents` (Phase 3+). Replay and conflict behavior are covered by API tests.

## Problem

Ingestion may be retried because of:

- Client timeouts while the server already accepted the upload
- Gateway retries
- Operator double-clicks in the UI
- Ambiguous network failures after `202` was generated but not received

Unbounded retries must not create unbounded shipments, documents, or verification runs.

## Mechanism: `Idempotency-Key`

### Header

| Header | Required for | Format |
|--------|--------------|--------|
| `Idempotency-Key` | `POST /v1/documents` | Opaque string, 8–128 chars, `[A-Za-z0-9._~-]+` recommended |

Clients generate a unique key per **logical** submit intent (e.g. UUID v4). Retries of the **same** intent reuse the same key.

### Scope

Idempotency is scoped to:

```text
(authenticated principal, Idempotency-Key)
```

For Part 1 single-tenant demos, principal may be a shared API key; the key still prevents duplicate processing for that key string.

Optional future: also bind to `customer_id` when multi-tenant auth lands.

### Server behavior

| Situation | Behavior |
|-----------|----------|
| First request with key K | Persist idempotency record + create shipment/document/run as designed; return **202** (or error) |
| Replay with same K and **same request fingerprint** | Return the **original** status and body (or an equivalent representation); do **not** start a second run |
| Replay with same K and **different** fingerprint | **409** `IDEMPOTENCY_KEY_REUSE_MISMATCH` |
| Missing key on `POST /v1/documents` | **400** `MISSING_IDEMPOTENCY_KEY` (Part 1: required) |

### Request fingerprint

At minimum, fingerprint includes:

- HTTP method + path
- `customer_id` (body/field)
- Document content digest (SHA-256 of uploaded bytes) **or** `source_path` + content hash when path-based intake is used
- Optional client `external_ref` if provided

Do **not** fingerprint volatile fields such as client timestamps.

## Domain-specific complement (optional)

In addition to `Idempotency-Key`, Part 1 **may** accept:

| Field | Purpose |
|-------|---------|
| `external_ref` | Caller’s stable reference (email Message-ID later, ERP id, etc.) |

Uniqueness recommendation (when both present):

```text
unique (customer_id, external_ref) WHERE external_ref IS NOT NULL
```

Rules:

- If `external_ref` collides with an existing document for the customer and content digest matches → treat as idempotent replay (same as key hit).
- If `external_ref` collides but digest differs → **409** `EXTERNAL_REF_CONFLICT`.

`Idempotency-Key` remains mandatory for HTTP retries; `external_ref` helps Part 2 email/file adapters (`REQ-PART2-001`, `REQ-PART2-002`).

## What “same processing” means

An idempotent replay must not:

- Create a second `document_id` / `run_id` for the same logical submit
- Re-bill duplicate LLM cost for an identical accepted ingest (implementation should short-circuit before extraction)

Re-processing **after** a terminal failure may be allowed via an explicit **new** idempotency key and/or a future `POST .../reprocess` endpoint (out of Part 1 API minimum). Do not overload silent POST retries into “force re-run.”

## Retention

Retain idempotency records at least **24 hours** (recommended **72 hours** for demo reliability). Expired keys may be reused; document the TTL in ops docs when implemented.

## Non-ingestion endpoints

| Endpoint class | Idempotency |
|----------------|-------------|
| GET retrieval | Naturally idempotent; no key required |
| `POST /v1/query` | **Not** persisted for replay by default; clients may retry safely because queries are read-only over persisted data. Optional future: cache by key for expensive NL interpretation |
| Health / ready | No key |

## Observability

Log/structured fields on ingest:

- `idempotency_key` (or hash thereof)
- `idempotency_replay` (boolean)
- `trace_id`, `run_id`, `document_id`, `shipment_id`

Never log raw document bytes.

## Security

- Treat idempotency keys as untrusted input (length limits, charset).
- Do not allow key replay to escalate into another tenant’s resources.
- Hashes in fingerprints are preferred over storing full payloads in the idempotency table.

## Related

- [contracts.md](./contracts.md) — `POST /v1/documents`
- [error-model.md](./error-model.md)
- Requirements: `REQ-DATA-003`, `REQ-EXT-001`
- Architecture principles: idempotency, failure isolation
