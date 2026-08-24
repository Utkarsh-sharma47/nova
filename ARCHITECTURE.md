# Architecture

High-level architecture for Nova.

## Purpose

Nova validates trade shipping documents with a multi-agent AI pipeline. Documents (for example Bill of Lading, invoice) are ingested, key fields are extracted, customer rules are applied, and the system produces a decision: auto-approve, human review, or request corrections.

## Current status

**Phase 3 (in progress):** document processing infrastructure (`nova.documents`) implements ADR-0006. Extractor/Validator/Router agents and UI remain unimplemented.

## Conceptual pipeline

```text
Document → ingestion → extraction → ExtractionResult
        → validation → ValidationResult
        → routing → DecisionResult
        → persistence → query/API → UI
```

Detail: [`docs/architecture/system-architecture.md`](docs/architecture/system-architecture.md).

## Technology stack (summary)

| Layer | Choice | ADR |
|-------|--------|-----|
| Backend | Python 3.12+, Pydantic, SQLAlchemy, Alembic | [0002](docs/decisions/0002-backend-stack.md) |
| API | FastAPI | [0004](docs/decisions/0004-api-framework.md) |
| DB | PostgreSQL 16 | [0003](docs/decisions/0003-database.md) |
| LLM | Provider-agnostic `LLMPort` | [0005](docs/decisions/0005-ai-provider-abstraction.md) |
| Documents | Pluggable processor/OCR port | [0006](docs/decisions/0006-document-processing.md) |
| Observability | Structured logs + metrics + health | [0007](docs/decisions/0007-observability.md) |
| Deploy | Docker Compose | [0008](docs/decisions/0008-deployment.md) |
| Frontend | React + TypeScript + Vite | [0009](docs/decisions/0009-frontend-stack.md) |

Index: [`docs/architecture/technology-stack.md`](docs/architecture/technology-stack.md).

## Design principles

See [`docs/architecture/principles.md`](docs/architecture/principles.md).

## Contracts

Authoritative Pydantic schemas: `src/nova/contracts/`.  
Docs: [`docs/architecture/contracts.md`](docs/architecture/contracts.md).

## Part 2 readiness

[`docs/architecture/part2-extension-points.md`](docs/architecture/part2-extension-points.md)

## Related documents

- [docs/architecture/](docs/architecture/)
- [docs/agents/](docs/agents/)
- [docs/database/](docs/database/)
- [docs/api/](docs/api/)
- [docs/decisions/](docs/decisions/)
- [AGENTS.md](AGENTS.md)
