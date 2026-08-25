# Architecture

High-level architecture for Nova.

## Purpose

Nova validates trade shipping documents with a multi-agent AI pipeline. Documents (for example Bill of Lading, invoice) are ingested, key fields are extracted, customer rules are applied, and the system produces a decision: auto-approve, human review, or request corrections.

## Current status

**Phase 11 production hardening** on top of Phases 3–10:

- Ingestion → `PipelineOrchestrator` → Extractor → Validator → Router → persistence
- Grounded `POST /v1/query`
- React/Vite ops UI (`frontend/`) with **runtime** `window.__NOVA_RUNTIME__` auth in Compose
- Compose `api` + `db` + `web` (non-root; Alembic-only schema — **no `create_all` in production**)
- Observability: `request_id` / `trace_id` / `run_id` / `agent_execution_id`, `/metrics`, `/health`, `/ready`
- Append-only extraction, validation, and decision history
- Document lifecycle through `extracted → validated → decided` (or `failed`)
- Remote deploy: **NOT EXECUTED** (procedure documented)

Detail: [`docs/architecture/end-to-end-pipeline.md`](docs/architecture/end-to-end-pipeline.md),
[`docs/architecture/frontend.md`](docs/architecture/frontend.md),
[`docs/deployment/`](docs/deployment/),
[`docs/audits/phase-11-production-readiness.md`](docs/audits/phase-11-production-readiness.md).


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
UI (React/Vite) → FastAPI routes
FastAPI routes → application services (ingestion + PipelineOrchestrator + ops + query)
                                      ├── persistence repositories → PostgreSQL
                                      ├── DocumentStoragePort → local filesystem
                                      ├── DocumentProcessorPort → PDF/text adapters
                                      ├── ExtractorService → LLMPort (MockLLM default)
                                      ├── ValidatorAgent → deterministic + optional LLM
                                      ├── RouterService → safety constraints + DecisionResult
                                      └── QueryService → allow-listed intents → repository
```

Routes contain no OCR, SQL, or agent policy details. The UI does not duplicate routing logic.

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
