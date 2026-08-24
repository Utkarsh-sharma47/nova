# ADR-0004: API framework (FastAPI)

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-08-25 |
| Deciders | Principal Software Architect (Phase 2) |
| Supersedes | — |
| Superseded by | — |

## Context

### Problem

Nova needs an HTTP API for ingestion, retrieval, validation/decision reads, NL query, and health.

### Requirements

- First-class OpenAPI from typed models
- Async-friendly I/O for LLM/document calls
- Align with Pydantic contracts ([ADR-0002](./0002-backend-stack.md))
- Keep LLM orchestration out of route handlers

## Decision

Use **FastAPI** as the HTTP framework.

```text
API routes → application services → domain/agents ports → infrastructure adapters
```

## Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| Flask / Quart | Simple | Weaker OpenAPI/typing |
| Django Ninja / DRF | Batteries included | Heavier; UI coupling temptation |
| Litestar | Modern typing | Smaller ecosystem |
| gRPC-only | Strong contracts | Poor browser ops UI fit |

## Consequences

### Advantages

Auto OpenAPI; DI fits ports/adapters; excellent Pydantic v2 integration.

### Disadvantages

Async misuse can hide blocking OCR/LLM calls.

### Operational cost

Low: one ASGI app.

### Complexity

Low–moderate with clear service layering.

### Developer velocity

High for typed endpoint iteration.

### Testing implications

httpx / TestClient once routes exist.

### Deployment implications

ASGI server; `/health` and `/ready`.

### Part 2 compatibility

Additional routers for email webhooks / approvals.

### Migration risk

Low within Python ASGI if services stay pure.

## Compliance

- API surface documented in `docs/api/` before implementation.
- No business agent logic inside route modules.

## References

- `REQ-QUERY-001`–`003`, `REQ-UI-001`, `REQ-OBS-001`
- [`docs/api/`](../api/)
