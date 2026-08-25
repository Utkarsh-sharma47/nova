# Roadmap

Phased delivery plan for Nova. Detail: [`docs/roadmap/roadmap.md`](docs/roadmap/roadmap.md).

## Phase 1 — Engineering foundation

Requirements inventory, product/problem/solution definition, Part 1 scope, Part 2 extension points, architecture principles, documentation system, git workflow, CI foundation (docs + secrets), AI agent governance, security baseline.

**Status:** Complete.

## Phase 2 — Stack selection & contracts

ADRs for language/runtime, API, DB, LLM abstraction, document processing, observability, deployment, frontend; typed agent/API contracts (`src/nova/contracts`); domain/DB/API/error/confidence/lifecycle docs; Python CI (Ruff, MyPy, contract pytest).

**Status:** Complete. Audit: [`docs/audits/phase-2-audit.md`](docs/audits/phase-2-audit.md).

## Phase 3 — Application foundation + document ingestion

Authenticated FastAPI upload/retrieval, idempotency, PostgreSQL/Alembic core records, local storage, PDF/text processors, request observability, Docker, and CI.

**Status:** Complete. Audit: [`docs/audits/phase-3-audit.md`](docs/audits/phase-3-audit.md).

## Phase 4 — Extractor Agent

`ExtractorService` + `LLMPort`/`MockLLM`, versioned prompts, schema-validated `ExtractionResult`, append-only extraction persistence.

**Status:** Complete.

## Phase 5 — Validator Agent

Deterministic + optional LLM validation, MATCH/MISMATCH/UNCERTAIN, evaluation harness.

**Status:** Complete. Audit: [`docs/audits/phase-5-audit.md`](docs/audits/phase-5-audit.md).

## Phase 6 — Router / Decision Agent

Fail-closed dispositions, decision evaluation (false AUTO_APPROVE = 0).

**Status:** Complete. Audit: [`docs/audits/phase-6-audit.md`](docs/audits/phase-6-audit.md).

## Phase 7 — End-to-end pipeline integration

`PipelineOrchestrator` wires extract → validate → route with append-only persistence and HTTP reads.

**Status:** Complete.

## Phase 8 — Grounded Query API

`POST /v1/query` with allow-listed intents and no LLM SQL.

**Status:** Complete.

## Phase 9 — Part 1 operations UI

React/TS/Vite ops UI, Compose `web` service, Vitest, demo fixtures.

**Status:** Complete.

## Phase 10–11 — System verification & production hardening

Compose hardening, observability, security gates, recovery runbook, production-readiness checklist.

**Status:** Complete (local). Remote deploy **NOT EXECUTED**. Audit: [`docs/audits/phase-11-production-readiness.md`](docs/audits/phase-11-production-readiness.md).

## Phase 12 — Final Part 1 release

Requirements audit, submission docs, demo runbook, evaluation proof, known limitations.

**Status:** Complete — verdict **PASS WITH LIMITATIONS**.

Artifacts: [`docs/audits/final-part1-audit.md`](docs/audits/final-part1-audit.md), [`docs/audits/final-release-checklist.md`](docs/audits/final-release-checklist.md), [`docs/audits/known-limitations.md`](docs/audits/known-limitations.md), [`docs/operations/demo-runbook.md`](docs/operations/demo-runbook.md).

## Part 2 — Forward (after Part 1)

**PLANNED — NOT IMPLEMENTED IN PART 1.**

Email/file triggers, multi-attachment, cross-document validation, draft replies, human approval actions, outbound sending.

## Change policy

Keep this file synchronized with `docs/roadmap/`. Significant scope changes deserve a note in [CHANGELOG.md](CHANGELOG.md). Technology choices belong in ADRs.
