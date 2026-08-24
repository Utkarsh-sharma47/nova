# API

HTTP interface documentation for Nova (Part 1 contracts).

## Current status

**Contracts defined (Phase 2). Runtime routes not implemented.**

Do not add FastAPI handlers in the same change set as these documents unless a later task explicitly requests implementation.

Implementation must follow:

1. Contracts in this directory
2. Stack ADRs in [`../decisions/`](../decisions/) (FastAPI per ADR-0004 when accepted)
3. Agent I/O schemas in [`../agents/`](../agents/)
4. Domain/persistence model in [`../database/`](../database/)

## Documents

| Document | Purpose |
|----------|---------|
| [contracts.md](./contracts.md) | Part 1 endpoint contracts (ingest, retrieve, validation, decision, query, health, ready) |
| [error-model.md](./error-model.md) | Common error envelope + HTTP status mapping |
| [versioning.md](./versioning.md) | `/v1` path versioning strategy |
| [idempotency.md](./idempotency.md) | `Idempotency-Key` for document ingestion |
| [query-interface.md](./query-interface.md) | NL query contract + **no arbitrary LLM SQL** security rule |

## Design summary

```text
UI / clients
    │
    ▼
HTTP /v1 (FastAPI — later)
    │
    ├─ POST /v1/documents          → ingestion port → run
    ├─ GET  /v1/documents/{id}
    ├─ GET  /v1/shipments/{id}
    ├─ GET  /v1/documents/{id}/validation
    ├─ GET  /v1/documents/{id}/decision
    └─ POST /v1/query              → allow-listed grounded plans only
GET /health , GET /ready           → ops (unversioned)
```

Routes call application services; they do **not** call LLM SDKs directly ([ADR-0004](../decisions/0004-api-framework.md)).

## Requirements covered

| REQ | API relevance |
|-----|----------------|
| REQ-EXT-001 | Document ingestion |
| REQ-DATA-001–003 | Retrieval + idempotent ingest |
| REQ-VAL-002–004 / REQ-VAL-006 | Validation results |
| REQ-ROUTER-001–003 | Decision results |
| REQ-QUERY-001–003 | Retrieval + NL query (no invented facts; no raw SQL from LLM) |
| REQ-OBS-001–002, REQ-OBS-004 | `trace_id` / error taxonomy |
| REQ-SEC-003 | Safe error/logging surface |

## Related

- [Architecture](../architecture/)
- [Agents](../agents/)
- [Security](../security/)
- [Observability](../observability/)
