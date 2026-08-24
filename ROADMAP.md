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

## Phase 6 — Query & UI

Query API, grounded NL query, minimal B2B operations UI (React/TS/Vite).

## Phase 7 — Hardening & Part 1 submission

Demo runbook, failure-path demo, simple deploy, submission completeness.

## Part 2 — Forward (after Part 1)

Email/file triggers, multi-attachment, cross-document validation, draft replies, human approval, outbound sending.

## Change policy

Keep this file synchronized with `docs/roadmap/`. Significant scope changes deserve a note in [CHANGELOG.md](CHANGELOG.md). Technology choices belong in ADRs.
