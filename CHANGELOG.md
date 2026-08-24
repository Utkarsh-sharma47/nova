# Changelog

All notable changes to this project will be documented in this file.

Format follows a simple Keep a Changelog style. Versions will be introduced when releases begin.

## [Unreleased]

### Added

- Phase 3 backend foundation (ingestion, no agents/LLM):
  - FastAPI app: `POST /v1/documents`, `GET /health`, `GET /ready`
  - SQLAlchemy models + Alembic `0001_phase3_foundation` migration
  - Local filesystem document storage (path-safe, no overwrite)
  - Idempotent ingest (`Idempotency-Key`) with queued verification runs
  - Docker Compose (api + Postgres 16); CI with Postgres service + image build
- Phase 2 technology architecture and domain contracts:
  - ADRs 0002–0010 (backend, database, API, LLM port, document processing, observability, deployment, frontend)
  - System/AI/layering architecture; error, confidence/evidence, lifecycle/idempotency models
  - Database domain model, relationships, indexing, audit model
  - API surface specs; Extractor/Validator/Router agent specifications
  - Pydantic contracts in `src/nova/contracts/` with schema tests
  - Docker/Compose skeleton; Python CI (Ruff, MyPy, pytest)
  - Phase 2 architecture audit
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
