# Roadmap

## Phase 1 — Engineering foundation

**Status:** Complete.

## Phase 2 — Stack selection & contracts

- Choose language/runtime, API framework, DB, LLM provider (ADRs)
- Define typed contracts for extraction, validation, routing
- Skeleton repo layout without full business logic
- Enable language-appropriate lint/type CI
- Testing and AI evaluation architecture (pyramid, failure/performance specs, eval framework, regression policy) — docs ahead of harness code
- ADRs 0002–0010
- Typed contracts (`src/nova/contracts` + agent/API docs)
- Domain/DB/API/observability/security/deployment architecture
- Python CI (Ruff, MyPy, contract pytest)

**Status:** Complete pending merge review. Audit: [`../audits/phase-2-architecture-audit.md`](../audits/phase-2-architecture-audit.md).

## Phase 3 — Ingestion & Extractor Agent

Document input, DocumentProcessor adapters, Extractor with confidence/evidence, observability.

## Phase 4 — Validation & Router

Customer rules, MATCH/MISMATCH/UNCERTAIN, router dispositions, golden fixtures, fail-safe defaults.

## Phase 5 — Persistence, samples, evaluation harness

SQLAlchemy/Alembic, samples, eval harness, idempotency.

## Phase 6 — Query & UI

Query API, grounded NL query, React/TS/Vite UI.

## Phase 7 — Hardening & Part 1 submission

Demo runbook, failure-path demo, deploy, submission package.

## Part 2 — Forward

Email/file triggers, multi-attachment, cross-doc validation, draft replies, human approval, outbound send.
