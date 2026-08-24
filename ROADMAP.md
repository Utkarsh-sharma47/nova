# Roadmap

Phased delivery plan for Nova. Detail: [`docs/roadmap/roadmap.md`](docs/roadmap/roadmap.md).

## Phase 1 — Engineering foundation

Requirements inventory, product/problem/solution definition, Part 1 scope, Part 2 extension points, architecture principles, documentation system, git workflow, CI foundation (docs + secrets), AI agent governance, security baseline.

**Status:** Complete.

## Phase 2 — Stack selection & contracts (current delivery)

ADRs for language/runtime, API, DB, LLM abstraction, document processing, observability, deployment, frontend; typed agent/API contracts (`src/nova/contracts`); domain/DB/API/error/confidence/lifecycle docs; Python CI (Ruff, MyPy, contract pytest).

**Exit criteria:** See [`docs/audits/phase-2-architecture-audit.md`](docs/audits/phase-2-architecture-audit.md).

## Phase 3 — Ingestion & Extractor

Document input, DocumentProcessor adapters, Extractor Agent with confidence/evidence, failure isolation, observability for extraction.

## Phase 4 — Validation & Router

Customer rules, MATCH/MISMATCH/UNCERTAIN, router dispositions, golden fixtures, fail-safe defaults.

## Phase 5 — Persistence, samples, evaluation

Persist core entities (SQLAlchemy/Alembic), clean + messy samples, eval harness, idempotency.

## Phase 6 — Query & UI

Query API, grounded NL query, minimal B2B operations UI (React/TS/Vite).

## Phase 7 — Hardening & Part 1 submission

Demo runbook, failure-path demo, simple deploy, submission completeness.

## Part 2 — Forward (after Part 1)

Email/file triggers, multi-attachment, cross-document validation, draft replies, human approval, outbound sending.

## Change policy

Keep this file synchronized with `docs/roadmap/`. Significant scope changes deserve a note in [CHANGELOG.md](CHANGELOG.md). Technology choices belong in ADRs.
