# ADR-0002: Backend stack (Python, Pydantic, SQLAlchemy, Alembic, pytest, Ruff, MyPy)

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-08-25 |
| Deciders | Principal Software Architect (Phase 2) |
| Supersedes | — |
| Superseded by | — |

## Context

### Problem

Nova needs a backend language and supporting libraries for typed contracts, AI orchestration, document processing, persistence, and testable deterministic policy code. Phase 1 deferred this choice.

### Requirements

- Typed stage contracts (`REQ-AI-*`, architecture principles)
- Strong ecosystem for LLM clients and document/OCR tooling
- Deterministic validation testability (`REQ-VAL-005`, `REQ-TEST-*`)
- Fast contributor/agent velocity for Part 1
- Part 2 extensibility without rewrite

## Decision

Use **Python 3.12+** as the backend language with:

| Concern | Library |
|---------|---------|
| Contracts / validation | **Pydantic v2** |
| ORM | **SQLAlchemy 2.x** |
| Migrations | **Alembic** |
| Tests | **pytest** (+ **pytest-asyncio** where async is used) |
| Lint / format | **Ruff** |
| Static types | **MyPy** (strict for `nova.contracts`) |
| Packaging | **`pyproject.toml`** with lockfile when dependencies stabilize |

API framework: [ADR-0004](./0004-api-framework.md). Database engine: [ADR-0003](./0003-database.md).

## Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| TypeScript (Node) end-to-end | One language with frontend | Weaker OCR/doc ML ecosystem |
| Go | Strong ops/perf | Slower AI/doc prototyping |
| Java / Kotlin | Enterprise persistence | Higher ceremony for Part 1 |
| Python without Pydantic | Fewer deps | Loses contract-first enforcement |

## Consequences

### Advantages

- Native fit for LLM SDKs, OCR, and data validation
- Pydantic models double as API and agent contracts
- Mature pytest ecosystem

### Disadvantages / trade-offs

- GIL limits CPU-bound parallelism (mitigate with process workers later if needed)
- Type discipline requires MyPy CI

### Operational cost

Low for Part 1: one runtime image.

### Complexity

Moderate; avoid premature Celery/queues.

### Developer velocity

High for extraction/validation prototypes and contract iteration.

### Testing implications

pytest contract tests validate Pydantic schemas in CI without LLM calls.

### Deployment implications

Single Python container; pin deps via lockfile.

### Part 2 compatibility

Async workers / extra ingestion adapters can be added as packages.

### Migration risk

Low if contracts remain the boundary. Switching language later would be high cost — intentional freeze now.

## Compliance

- Domain contracts live under `src/nova/contracts/` as Pydantic models.
- Do not call LLM providers from API route handlers.
- Enable Ruff + MyPy + pytest in CI for the Python tree.

## References

- `REQ-AI-001`–`006`, `REQ-TEST-001`–`004`, `REQ-VAL-005`
- [`docs/architecture/technology-stack.md`](../architecture/technology-stack.md)
- [ADR-0010](./0010-ai-agent-contracts-and-trust-model.md)
