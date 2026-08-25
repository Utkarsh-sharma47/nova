# Changelog

All notable changes to this project will be documented in this file.

Format follows a simple Keep a Changelog style. Versions will be introduced when releases begin.

## [Unreleased]

### Added

- Phase 3 document processing infrastructure:
  - `DocumentProcessorPort`, intake validation, `DocumentProcessingService`
  - `digital_pdf` (pypdf) and `passthrough_text` adapters (no OCR)
  - Local blob store, security controls, observability, benchmarks
  - Docs under `docs/documents/` and architecture/testing guides

### Added

- Phase 3 operational foundation:
  - FastAPI API shell with `/health`, `/ready`, `/metrics`
  - Docker Compose (API + PostgreSQL), non-root Dockerfile, entrypoint migrations
  - Alembic bootstrap (`schema_meta`)
  - Structured JSON logging with request/trace IDs; Prometheus baseline metrics (`prometheus_client`)
  - Document processing counters wired through `nova.documents.observability`
  - Compose API `DATABASE_URL` forced to service host `db` (from `POSTGRES_*`)
  - CI: Ruff, MyPy, pytest, pip-audit, Docker build, migration validation, Dockerfile/secret checks
  - Ops tests + `scripts/verify-compose.sh`
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
