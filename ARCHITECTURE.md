# Architecture

High-level architecture for Nova.

## Purpose

Nova validates trade shipping documents with a multi-agent AI pipeline. Documents (for example Bill of Lading, invoice) are ingested, key fields are extracted, customer rules are applied, and the system produces a decision: auto-approve, human review, or request corrections.

## Current status

**Phase 4 Extractor implemented** on top of Phase 3 foundation: ingestion
queues a run, then `ExtractorService` (via `LLMPort`, default `MockLLM`)
produces schema-validated `ExtractionResult` with presence/confidence/evidence.
Append-only `extracted_fields` / `agent_executions` / `model_call_metadata`
support audit. Validator, Router, live vendor adapters, and UI remain out of
scope.

## Conceptual pipeline

```text
Document → ingestion → extraction → ExtractionResult
        → validation → ValidationResult
        → routing → DecisionResult
        → persistence → query/API → UI
```

Detail: [`docs/architecture/system-architecture.md`](docs/architecture/system-architecture.md).

## Implemented dependency direction

```text
FastAPI routes → application ingestion service → domain policy
                                      ├── persistence repositories → PostgreSQL
                                      ├── DocumentStoragePort → local filesystem
                                      ├── DocumentProcessorPort → PDF/text adapters
                                      └── ExtractorService → LLMPort (MockLLM default)
```

Routes contain no OCR or SQL details. Document bytes are validated for size,
extension, content signature, and safe filename before storage. Ingestion
commits document, immutable first version, queued run, and idempotency record as
one database transaction; raw bytes remain outside PostgreSQL. Extraction then
runs (Part 1: synchronous post-accept) and appends AI outputs without overwriting
prior runs.

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

| Layer | Source of truth |
|-------|-----------------|
| Agent semantics (safety rules, presence, decisions) | [`docs/agents/contracts.md`](docs/agents/contracts.md), [`docs/agents/trust-model.md`](docs/agents/trust-model.md), [ADR-0010](docs/decisions/0010-ai-agent-contracts-and-trust-model.md) |
| Runtime schema encoding | `src/nova/contracts/` (Pydantic) — must implement agent semantics |
| Cross-layer alignment | [`docs/architecture/contract-alignment.md`](docs/architecture/contract-alignment.md) |
| HTTP API | [`docs/api/contracts.md`](docs/api/contracts.md) |
| Persistence | [`docs/database/`](docs/database/) |

Docs index: [`docs/architecture/contracts.md`](docs/architecture/contracts.md).

## Part 2 readiness

[`docs/architecture/part2-extension-points.md`](docs/architecture/part2-extension-points.md)

## Related documents

- [docs/architecture/](docs/architecture/)
- [docs/agents/](docs/agents/)
- [docs/database/](docs/database/)
- [docs/api/](docs/api/)
- [docs/decisions/](docs/decisions/)
- [AGENTS.md](AGENTS.md)
