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

## Phase 3 — Application foundation + document ingestion

**Status:** Complete pending merge review. Audit: [`../audits/phase-3-audit.md`](../audits/phase-3-audit.md).

Authenticated FastAPI ingest/retrieval, PostgreSQL/Alembic core entities,
idempotency, local storage, PDF/text `DocumentProcessorPort`, observability,
Docker Compose, CI. **Extractor Agent is deferred to Phase 4** (verification
runs are queued only).

## Phase 4 — Extraction, Validation & Router

Extractor Agent against frozen contracts, then customer rules,
MATCH/MISMATCH/UNCERTAIN, router dispositions, golden fixtures, fail-safe defaults.

## Phase 5 — Persistence expansion, samples, evaluation harness

Validation/decision/audit persistence, samples, eval harness. Core ingestion
entities and HTTP idempotency landed in Phase 3.

## Phase 6 — Query & UI

Query API, grounded NL query, React/TS/Vite UI.

## Phase 7 — Hardening & Part 1 submission

Demo runbook, failure-path demo, deploy, submission package.

## Part 2 — Forward

Email/file triggers, multi-attachment, cross-doc validation, draft replies, human approval, outbound send.
