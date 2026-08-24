# Roadmap

## Phase 1 — Engineering foundation

**Status:** Complete.

## Phase 2 — Stack selection & contracts

- ADRs 0002–0010
- Typed contracts (`src/nova/contracts` + agent/API docs)
- Domain/DB/API/observability/security/deployment architecture
- Python CI (Ruff, MyPy, contract pytest)

**Status:** Complete. Audit: [`../audits/phase-2-architecture-audit.md`](../audits/phase-2-architecture-audit.md).

## Phase 3 — Operational foundation

Compose deploy, Dockerfile, Alembic bootstrap, structured logs/metrics, health/ready, CI security & docker/migration checks.

**Status:** Delivered (`feature/phase-3-ops-quality`).

## Phase 3 (product) — Ingestion & Extractor Agent

Document input, DocumentProcessor adapters, Extractor with confidence/evidence, observability.

## Phase 4 — Validation & Router

Customer rules, MATCH/MISMATCH/UNCERTAIN, router dispositions, golden fixtures, fail-safe defaults.

## Phase 5 — Persistence, samples, evaluation harness

Full domain SQLAlchemy/Alembic, samples, eval harness, idempotency.

## Phase 6 — Query & UI

Query API, grounded NL query, React/TS/Vite UI.

## Phase 7 — Hardening & Part 1 submission

Demo runbook, failure-path demo, deploy, submission package.

## Part 2 — Forward

Email/file triggers, multi-attachment, cross-doc validation, draft replies, human approval, outbound send.
