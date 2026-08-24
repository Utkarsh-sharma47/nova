# Changelog

All notable changes to this project will be documented in this file.

Format follows a simple Keep a Changelog style. Versions will be introduced when releases begin.

## [Unreleased]

### Added

- Phase 4 Extractor Agent (`0.4.0`):
  - `LLMPort` + `MockLLM` (default test/local provider; no API key required)
  - `ExtractorService` with versioned prompt `extractor.v1`, 60s timeout, max 2 retries
  - Presence/confidence/evidence anti-fabrication and schema validation
  - Append-only `agent_executions`, `model_call_metadata`, `extracted_fields`
  - Document lifecycle `content_available → in_pipeline → extracted|failed`
  - Unit, integration, and security tests under `tests/extraction/`
- Phase 3 application foundation (`0.3.0`):
  - FastAPI health/readiness, authenticated ingestion, and document/shipment retrieval
  - Required HTTP idempotency with replay and mismatch conflict behavior
  - SQLAlchemy repositories and full Alembic migration for ingestion records
  - Safe local filesystem storage and digital PDF / UTF-8 text processors
  - Structured request correlation logs and safe API error envelopes
  - Non-root Docker/Compose runtime with migration entrypoint and PostgreSQL health checks
  - Unit, API, failure/security, and optional PostgreSQL migration tests
  - Phase 3 integration audit (`docs/audits/phase-3-audit.md`) — PASS
- Phase 3 queues verification runs; Phase 4 adds Extractor (Validator/Router still deferred).
- Phase 2 technology stack ADRs (backend, database, API, AI provider, document processing, observability, deployment, frontend)
- Phase 2 Pydantic contract package (`src/nova/contracts/`) with contract tests and Python CI
- Phase 2 domain and database architecture:
  - Entity domain model (`Customer` … `AuditEvent`) with data classification
  - PostgreSQL schema design, relationships/ER diagram, indexing, audit model
  - Database test plan (constraints, duplicates, transactions, idempotency)
  - Persistence ADR (PostgreSQL as system of record)
- Phase 2 AI agent contracts and trust model (Extractor, Validator, Router); agent evaluation specification (no harness yet)
- Phase 2 Part 1 HTTP API contracts (ingestion, retrieval, validation, decision, NL query, health/ready)
- Phase 2 integration audit (`docs/audits/phase-2-audit.md`) — PASS
- Testing and AI evaluation architecture:
  - Test pyramid (unit, contract, integration, E2E, evaluation, regression, failure, performance)
  - Contract, failure, and performance testing specs (no harness/tooling yet)
  - Evaluation framework, dataset categories, metrics (thresholds as calibration targets)
  - Mandatory fixed-dataset regression policy for prompt/model/policy changes
- Phase 1 engineering foundation:
  - Requirements inventory with stable `REQ-*` IDs (assignment vs engineering)
  - Acceptance criteria, traceability, and scope boundaries
  - Product problem/solution/personas definitions
  - Part 1 scope and Part 2 extension points
  - Architecture principles, overview, and engineering standards
  - Testing / evaluation / observability / deployment philosophies
  - Security baseline; `.gitignore`; `.env.example`
  - Git workflow documentation and PR template
  - AI development governance (`AGENTS.md` + `docs/ai-development/`)
  - CI foundation: docs-structure and secret-pattern checks
  - ADR-0001 (documentation-first Phase 1)
- Documentation system under `docs/` with section READMEs and templates
