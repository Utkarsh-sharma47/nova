# ADR-0003: PostgreSQL as system of record

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-08-25 |
| Deciders | Domain / database architecture (Phase 2) |
| Supersedes | — |
| Superseded by | — |

## Context

Nova must persist shipments, documents, extraction results (with confidence and evidence), validation outcomes, and routing decisions for audit, query, and human review (`REQ-DATA-001`). The model must support **multiple documents per shipment** now (`REQ-DATA-002`, Part 2 extension points) and remain amenable to idempotent re-processing (`REQ-DATA-003`).

Phase 1 left persistence technology undecided. Structured AI outputs must remain **queryable**—not only free-form LLM text. Relational constraints (foreign keys, uniqueness, partial uniques) are central to preventing duplicate documents and silent integrity loss.

## Decision

Use **PostgreSQL** as Nova’s primary system of record for domain and audit data.

- Document **bytes** live in object storage (URI + hash on `document_versions`); PostgreSQL stores metadata and structured pipeline outputs.
- Schema design, indexing, and audit strategy are documented under `docs/database/`.
- Application repositories and migrations are **out of scope** for this ADR’s delivery; they follow in later phases against this contract.

## Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| PostgreSQL | Strong FK/unique constraints, JSONB for evidence, mature ops, fits audit + relational domain | Requires migration discipline |
| SQLite only | Simple local demo | Weaker concurrent ops story; awkward for multi-user B2B review later |
| Document DB (e.g. MongoDB) as primary | Flexible documents | Weaker declarative integrity for FKs/uniques; easier to lose cross-run consistency |
| Dual-write relational + warehouse now | Analytics-ready | Premature complexity for Part 1 |

## Consequences

### Positive

- Enforce shipment→documents, idempotency keys, and decision fail-safe checks in the database.
- JSONB supports evidence and reasoning without abandoning typed columns for enums and confidence.
- Clear path to Part 2 tables (ingestion messages, drafts, approvals, outbound) without rewriting Part 1 history.

### Negative / trade-offs

- Team must run PostgreSQL (local container acceptable) before persistence phase completes.
- JSONB still requires application-level schema validation.
- Object storage remains a second moving part for blobs.

### Follow-up work

- Phase 5: migrations, repositories, integration tests per [database-test-plan.md](../database/database-test-plan.md).
- Confirm object-storage choice in a separate ADR when implementing ingestion.
- Enable DB-backed CI (e.g. testcontainers) when application tests exist.

## Compliance

- Do not introduce a second primary store for the same domain entities without a new ADR.
- Do not collapse multi-document cardinality in migrations.
- Keep AI stage outputs append-only as specified in the domain model.
- Update `docs/database/*` when the physical schema changes.

## References

- [domain-model.md](../database/domain-model.md)
- [schema-design.md](../database/schema-design.md)
- [relationships.md](../database/relationships.md)
- Requirements: `REQ-DATA-*`, `REQ-PART2-003`, `REQ-AI-006`, `REQ-VAL-006`
- Architecture principles: auditability, idempotency, Part 2 extensibility
