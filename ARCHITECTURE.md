# Architecture

High-level architecture for Nova.

## Purpose

Nova validates trade shipping documents with a multi-agent AI pipeline. Documents (for example Bill of Lading, invoice) are ingested, key fields are extracted, customer rules are applied, and the system produces a decision: auto-approve, human review, or request corrections.

## Current status

Documentation foundation plus **domain/database architecture**. PostgreSQL is the accepted system of record ([ADR-0002](docs/decisions/0002-postgresql-persistence.md)). No runtime services, migrations, or agent implementations are in this phase.

## Conceptual pipeline

```text
Document → ingestion → extraction → confidence/evidence
        → validation → routing → persistence → query → UI
```

Persistence stores shipment-centric, multi-document data. See [`docs/database/`](docs/database/).

## Design principles

- **Contracts first.** Agent inputs/outputs and external interfaces should be explicit and versioned.
- **Human-in-the-loop.** Ambiguous or high-risk cases escalate to review rather than silent auto-approval.
- **Auditability.** Decisions should be explainable from stored fields, rule results, and audit events.
- **Idempotency.** Re-ingest and re-run keys must be safe under unique constraints.
- **Part 2 extensibility.** Shipment 1→N documents; reserved tables for email, drafts, approvals, outbound.
- **Scoped evolution.** Subsystems change via ADRs; avoid silent architectural drift.
- **Security by default.** Treat document contents as sensitive; see [SECURITY.md](SECURITY.md).

## Persistence (decided)

| Concern | Decision |
|---------|----------|
| Primary store | PostgreSQL (ADR-0002) |
| Document bytes | Object storage via URI + content hash on `document_versions` |
| Domain model | [`docs/database/domain-model.md`](docs/database/domain-model.md) |
| Schema | [`docs/database/schema-design.md`](docs/database/schema-design.md) |

## Documentation structure

Detailed architecture notes live under [`docs/architecture/`](docs/architecture/). Data model under [`docs/database/`](docs/database/). Agent design under [`docs/agents/`](docs/agents/).

## Open decisions

Still to be recorded as ADRs before coding:

- Language/runtime and API framework
- Object storage provider
- LLM provider
- Orchestration model for agents
- Rules DSL / exact `definition_json` schemas
- API surface for intake and review
- Evaluation harness tooling

## Related documents

- [docs/architecture/](docs/architecture/)
- [docs/database/](docs/database/)
- [docs/agents/](docs/agents/)
- [docs/decisions/](docs/decisions/)
- [ADR-0002](docs/decisions/0002-postgresql-persistence.md)
- [AGENTS.md](AGENTS.md)
