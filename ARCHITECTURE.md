# Architecture

High-level architecture for Nova (Part 1 implemented).

## Purpose

Nova validates trade shipping documents with a multi-agent AI pipeline. Documents (for example Bill of Lading, invoice) are ingested, key fields are extracted, customer rules are applied, and the system produces a decision: auto-approve, human review, or request corrections.

## Current status

**Phase 12 final Part 1 release** (audit: [`docs/audits/final-part1-audit.md`](docs/audits/final-part1-audit.md)):

- Ingestion → `PipelineOrchestrator` → Extractor → Validator → Router → persistence
- Grounded `POST /v1/query` (allow-listed intents; **no LLM SQL**)
- React/Vite ops UI with runtime auth config in Compose
- Compose `api` + `db` + `web` (non-root; Alembic-only schema — **no `create_all` in production**)
- Observability: `request_id` / `trace_id` / `run_id` / `agent_execution_id`, `/metrics`, `/health`, `/ready`
- Append-only extraction, validation, and decision history
- Remote deploy: **NOT EXECUTED** (procedure documented)

## Architecture diagram

```text
                    PART 1 IMPLEMENTED
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React/Vite)                     │
│         dashboard · upload · document · shipment · query          │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTPS / JSON
┌───────────────────────────────▼─────────────────────────────────┐
│                         FastAPI (API)                             │
│  /v1/documents · validation · decision · query · ops              │
│  /health · /ready · /metrics                                      │
└───────┬─────────────────┬─────────────────┬─────────────────────┘
        │                 │                 │
        │         ┌───────▼───────┐         │
        │         │   Pipeline    │         │
        │         │ Orchestrator  │         │
        │         └───────┬───────┘         │
        │                 │                 │
        │    ┌────────────┼────────────┐    │
        │    ▼            ▼            ▼    │
        │ Extractor   Validator     Router  │
        │ (LLMPort)  (rules+LLM)  (policy)  │
        │    │            │            │    │
┌───────▼────▼────────────▼────────────▼────▼─────────────────────┐
│                     PostgreSQL (system of record)                 │
│        documents · extractions · validations · decisions          │
│                    append-only AI history                         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Grounded Query      │
                    │  (repository reads)   │
                    └───────────────────────┘

┌──────────────────┐   ┌──────────────────────────────────────────┐
│ Document Storage │   │ Observability                             │
│ local filesystem │   │ structured logs · correlation IDs · metrics│
└──────────────────┘   └──────────────────────────────────────────┘

              PART 2 EXTENSION POINTS (NOT IMPLEMENTED)
   email/file ingestion · multi-doc · cross-doc validation
   human approval UX · amendment/outbound communication
```

## Conceptual pipeline

```text
Document → ingestion → extraction → ExtractionResult
        → validation → ValidationResult
        → routing → DecisionResult
        → persistence → query/API → UI
```

Detail: [`docs/architecture/end-to-end-pipeline.md`](docs/architecture/end-to-end-pipeline.md).

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

## Part 2 readiness

**PLANNED — NOT IMPLEMENTED IN PART 1.**

[`docs/architecture/part2-extension-points.md`](docs/architecture/part2-extension-points.md)

## Related documents

- [docs/architecture/](docs/architecture/)
- [docs/agents/](docs/agents/)
- [docs/database/](docs/database/)
- [docs/api/](docs/api/)
- [docs/decisions/](docs/decisions/)
- [docs/audits/](docs/audits/)
- [AGENTS.md](AGENTS.md)
