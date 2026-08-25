# ADR-0003: Database (PostgreSQL)

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-08-25 |
| Deciders | Principal Software Architect (Phase 2) |
| Supersedes | — |
| Superseded by | — |

## Context

### Problem

Nova must persist shipments, documents, extractions, validations, decisions, and audit events with relational integrity (`REQ-DATA-*`, `REQ-QUERY-*`).

### Requirements

- 1:N shipment → documents (Part 2 ready)
- Auditable validation/decision history
- Idempotent reprocessing support
- Simple Part 1 deploy
- SQLAlchemy/Alembic compatibility ([ADR-0002](./0002-backend-stack.md))

## Decision

Use **PostgreSQL 16** as the system of record.

- Access via SQLAlchemy 2.x; schema evolution via Alembic (implemented in Phase 5+).
- UUID primary keys.
- JSONB only for explicitly versioned flexible payloads, not as a substitute for core relational entities.
- Local: Docker Compose Postgres.

Document **bytes** live in object storage (URI + content hash on `document_versions`); PostgreSQL stores metadata and structured pipeline outputs.

## Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| SQLite | Zero ops | Weak concurrent write |
| MySQL / MariaDB | Familiar | Weaker JSONB ergonomics for our patterns |
| MongoDB | Flexible docs | Weak relational audit joins |
| DynamoDB | Serverless scale | Awkward Part 2 joins |

## Consequences

### Advantages

Strong constraints, indexes, transactions; JSONB when needed.

### Disadvantages

Requires a running database service.

### Operational cost

Low–moderate: one Postgres instance for Part 1.

### Complexity

Low for single-service deploy.

### Developer velocity

High with SQLAlchemy + Alembic once models exist.

### Testing implications

Integration tests may use testcontainers/Compose; contract tests do not need DB.

### Deployment implications

Compose/`DATABASE_URL`; readiness checks against DB.

### Part 2 compatibility

Multi-doc shipments, approval state, communications via migrations.

### Migration risk

Low within SQL; leaving Postgres later is costly — freeze now.

## Compliance

- Domain model in `docs/database/` before ORM implementation.
- No production ORM models in Phase 2 (design only).
- Secrets for DB credentials only via env / secret store.

## References

- `REQ-DATA-001`–`004`, `REQ-PART2-003`
- [`docs/database/domain-model.md`](../database/domain-model.md)
