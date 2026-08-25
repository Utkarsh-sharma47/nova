# Roadmap

Phased delivery plan for Nova. Detail: [`docs/roadmap/roadmap.md`](docs/roadmap/roadmap.md).

## Phase 1 — Engineering foundation

Requirements inventory, product/problem/solution definition, Part 1 scope, Part 2 extension points, architecture principles, documentation system, git workflow, CI foundation (docs + secrets), AI agent governance, security baseline.

**Status:** Complete.

## Phase 2 — Stack selection & contracts

ADRs for language/runtime, API, DB, LLM abstraction, document processing, observability, deployment, frontend; typed agent/API contracts (`src/nova/contracts`); domain/DB/API/error/confidence/lifecycle docs; Python CI (Ruff, MyPy, contract pytest).

**Exit criteria:** See [`docs/audits/phase-2-architecture-audit.md`](docs/audits/phase-2-architecture-audit.md).

- **Done (docs):** PostgreSQL system of record + domain/schema design ([`docs/database/`](docs/database/))
- **Done (docs):** AI agent contracts and trust model ([`docs/agents/`](docs/agents/))
- **Done (docs):** Part 1 HTTP API contracts ([`docs/api/`](docs/api/))
- Record remaining stack ADRs; freeze interfaces for extraction, validation, and decisioning

## Phase 3 — Application foundation + document ingestion

**Application foundation and document ingestion complete:** authenticated
FastAPI upload/retrieval, idempotency, PostgreSQL/Alembic core records, local
storage, PDF/text processors, request observability, Docker, and CI.

Audit: [`docs/audits/phase-3-audit.md`](docs/audits/phase-3-audit.md).

Extractor Agent work is explicitly deferred; Phase 3 ingestion only queues a
verification run and must not be read as an extraction implementation.

## Phase 4 — Extraction, Validation & Router

**Extractor (delivered on `feature/phase-4-extractor`):** `ExtractorService` +
`LLMPort`/`MockLLM`, versioned prompts, schema-validated `ExtractionResult`,
append-only extraction persistence, lifecycle
`content_available → in_pipeline → extracted|failed`.

Still deferred: Validator, Router, golden eval harness, live vendor LLM adapters.

## Phase 5 — Persistence expansion, samples, evaluation

Persist validation/decision/audit entities, clean + messy samples, and add the
evaluation harness. Core ingestion entities and HTTP idempotency landed in Phase 3.

## Phase 6 — Query & UI (split)

Query API and UI were delivered as Phases 8–9 after pipeline integration.

## Phase 7 — End-to-end pipeline integration

**Implemented on `feature/phase-7-pipeline-integration`:** Part 1 orchestrator wires
ingestion → extraction → validation → routing with append-only persistence,
fail-closed semantics, and wired validation/decision HTTP reads.

## Phase 8 — Grounded Query API

**Implemented:** `POST /v1/query` with allow-listed intents and no LLM SQL.

## Phase 9 — Part 1 operations UI

**Implemented on `feature/phase-9-frontend`:** React/TS/Vite ops UI, Compose `web`
service, Vitest coverage, and demo runbook for synthetic fixtures.


## Phase 11 — Deployment, security hardening, observability, production readiness

**Branch:** `feature/phase-11-production-hardening`.

- Harden Compose topology (`api` + `db` + `web`): non-root containers, health/ready/metrics
- Runtime web auth via `window.__NOVA_RUNTIME__` (no baked production tokens)
- Configuration reference + production startup gates; Alembic-only schema (no `create_all`)
- Request/upload limits, CORS production rules, dependency audits in CI
- Recovery runbook + `scripts/verify-production-readiness.sh`
- Docs under `docs/deployment/`, `docs/security/`, `docs/observability/`, `docs/operations/recovery.md`
- Audit checklist: [`docs/audits/phase-11-production-readiness.md`](docs/audits/phase-11-production-readiness.md)

**Remote / cloud production deploy: NOT EXECUTED** (procedure documented only).

## Part 2 — Forward (after Part 1)

Email/file triggers, multi-attachment, cross-document validation, draft replies, human approval, outbound sending.

## Change policy

Keep this file synchronized with `docs/roadmap/`. Significant scope changes deserve a note in [CHANGELOG.md](CHANGELOG.md). Technology choices belong in ADRs.
