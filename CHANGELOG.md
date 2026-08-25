# Changelog

All notable changes to this project will be documented in this file.

Format follows a simple Keep a Changelog style. Versions will be introduced when releases begin.

## [Unreleased]

### Added

- Phase 11 production hardening:
  - Compose deploy docs (architecture, configuration, local, frontend, production, CI/CD)
  - Non-root API + nginx-unprivileged web; runtime `__NOVA_RUNTIME__` auth (no baked tokens)
  - Request body limits, production config gates, CORS/upload security docs
  - Observability docs (request/trace/run/agent IDs, metrics, health, JSON log fields)
  - Recovery runbook + `scripts/verify-production-readiness.sh`
  - Phase 11 production-readiness audit checklist (`docs/audits/phase-11-production-readiness.md`)
  - Remote production deploy marked **NOT EXECUTED**


- Phase 9 Part 1 operations UI (`0.9.0`):
  - React + TypeScript + Vite app in `frontend/`
  - Dashboard, upload, document/shipment detail, grounded query pages
  - Typed API client with structured error/`trace_id` handling
  - Vitest component tests; Docker/nginx Compose `web` service
  - Justified ops APIs: `GET /v1/ops/summary`, `GET /v1/documents`, `POST /v1/customers`
  - Phase 8 query service adapted onto Phase 7 validation/decision persistence
  - Synthetic demo fixture + runbook `docs/operations/ui-demo.md`
- Phase 7 end-to-end pipeline integration:
  - `PipelineOrchestrator` coordinates extract → validate → route after ingestion
  - Document lifecycle `extracted → validated → decided` (or `failed`)
  - SQL `validations` table + wired `GET .../validation` and `GET .../decision`
  - Shipment aliases for validation/decision reads
  - Fail-closed stage semantics; append-only AI history preserved across stage failures
  - E2E suite `tests/pipeline/` (20+ scenarios, MockLLM only)
  - Local baseline script `scripts/benchmark_pipeline.py`
  - Docs: `docs/architecture/end-to-end-pipeline.md`
- Phase 4 Extractor Agent (`0.4.0`):
  - `LLMPort` + `MockLLM` (default test/local provider; no API key required)
  - `ExtractorService` with versioned prompt `extractor.v1`, 60s timeout, max 2 retries
  - Presence/confidence/evidence anti-fabrication and schema validation
  - Append-only `agent_executions`, `model_call_metadata`, `extracted_fields`
  - Document lifecycle `content_available → in_pipeline → extracted|failed`
  - Unit, integration, and security tests under `tests/extraction/`
- Phase 5 Validator Agent (`nova.validator` / `nova.agents.validator`):
  - Deterministic rules + optional LLM judgment with fail-closed safety
  - Append-only validation persistence port
- Phase 6 Router / Decision Agent (`nova.router`):
  - Deterministic safety constraints; AUTO_APPROVE only when fully eligible
  - Optional advisory LLM assist that cannot authorize AUTO_APPROVE
  - System failsafe → HUMAN_REVIEW; `system_failsafe` cannot store AUTO_APPROVE
  - Append-only `decisions` table
  - Decision evaluation harness (false AUTO_APPROVE target 0.0)
- Phase 3 application foundation (`0.3.0`):
  - FastAPI health/readiness, authenticated ingestion, and document/shipment retrieval
  - Required HTTP idempotency with replay and mismatch conflict behavior
  - SQLAlchemy repositories and full Alembic migration for ingestion records
  - Safe local filesystem storage and digital PDF / UTF-8 text processors
  - Structured request correlation logs and safe API error envelopes
  - Non-root Docker/Compose runtime with migration entrypoint and PostgreSQL health checks
  - Unit, API, failure/security, and optional PostgreSQL migration tests
  - Phase 3 integration audit (`docs/audits/phase-3-audit.md`) — PASS
- Phase 3 queues verification runs; Phase 7 runs the full extract→validate→route pipeline.
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
