# API

HTTP API design for Nova.

**Phase 3 implements:** `POST /v1/documents` (multipart ingest, `202` + idempotency), `GET /health`, `GET /ready`. Retrieval, validation, decision, and query endpoints remain contract-only until later phases.

| Doc | Purpose |
|-----|---------|
| [surface.md](./surface.md) | Endpoint index |
| [endpoints.md](./endpoints.md) | Per-endpoint notes |
| [contracts.md](./contracts.md) | Request/response shapes |
| [error-model.md](./error-model.md) | HTTP errors |
| [idempotency.md](./idempotency.md) | Idempotency |
| [versioning.md](./versioning.md) | API versioning |
| [query-interface.md](./query-interface.md) | NL query |

Framework: FastAPI ([ADR-0004](../decisions/0004-api-framework.md)). Code: `src/nova/api/`.
