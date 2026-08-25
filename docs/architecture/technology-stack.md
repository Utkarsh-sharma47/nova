# Technology stack (Phase 2)

Selected stack for Part 1 Nova. Each choice is justified in an ADR. This document is the index; ADRs are authoritative.

## Selected stack

| Layer | Choice | ADR |
|-------|--------|-----|
| Language / runtime | Python 3.12+ | [ADR-0002](../decisions/0002-backend-stack.md) |
| API framework | FastAPI | [ADR-0004](../decisions/0004-api-framework.md) |
| Validation / contracts | Pydantic v2 | ADR-0002, ADR-0004 |
| ORM / migrations | SQLAlchemy 2.x + Alembic | [ADR-0003](../decisions/0003-database.md) |
| Database | PostgreSQL 16 | ADR-0003 |
| Testing | pytest (+ pytest-asyncio) | ADR-0002 |
| Lint / format | Ruff | ADR-0002 |
| Types | MyPy (strict for contracts) | ADR-0002 |
| Frontend | React + TypeScript + Vite | [ADR-0009](../decisions/0009-frontend-stack.md) |
| Containers | Docker (+ Compose for local) | [ADR-0008](../decisions/0008-deployment.md) |
| LLM access | Provider-agnostic port | [ADR-0005](../decisions/0005-ai-provider-abstraction.md) |
| Document processing | Pluggable extract/OCR adapters | [ADR-0006](../decisions/0006-document-processing.md) |
| Observability | Structured logs + metrics + health | [ADR-0007](../decisions/0007-observability.md) |

## Evaluation method

For each major choice we recorded: problem, requirements, selection, alternatives, advantages/disadvantages, operational cost, complexity, developer velocity, testing implications, deployment implications, Part 2 compatibility, and migration risk.

## Explicit non-choices (Part 1)

| Rejected / deferred | Why |
|---------------------|-----|
| Microservices / message bus as core | Overkill for Part 1 demo; adds ops cost without REQ pressure |
| Hard-coding a single LLM vendor in domain code | Blocks provider swap and eval A/B |
| NoSQL as primary store | Relational audit model (shipment → docs → checks → decisions) fits SQL |
| Django monolith | Heavier admin/UI coupling; FastAPI + separate React UI fits ops UI better |
| GraphQL for Part 1 | REST is enough for the small API surface |

## Skeleton layout (Phase 2)

```text
src/nova/
  contracts/          # Pydantic domain contracts (implemented)
  # domain/, api/, agents/, infra/ reserved for later phases
tests/contracts/      # Schema/contract tests
docs/                 # Architecture & ADRs
Dockerfile            # Deployment shape (no business logic)
docker-compose.yml    # Local API + Postgres shape
```

Application business logic, agents, ORM models, and UI are **not** implemented in Phase 2.
