# Changelog

All notable changes to this project will be documented in this file.

Format follows a simple Keep a Changelog style. Versions will be introduced when releases begin.

## [Unreleased]

### Added

- Phase 2 technology stack ADRs (backend, database, API, AI provider, document processing, observability, deployment, frontend)
- Phase 2 Pydantic contract package (`src/nova/contracts/`) with contract tests and Python CI
- Phase 2 domain and database architecture:
  - Entity domain model (`Customer` … `AuditEvent`) with data classification
  - PostgreSQL schema design, relationships/ER diagram, indexing, audit model
  - Database test plan (constraints, duplicates, transactions, idempotency)
  - Persistence ADR (PostgreSQL as system of record)
- Phase 2 AI agent contracts and trust model (Extractor, Validator, Router); agent evaluation specification (no harness yet)
- Phase 2 Part 1 HTTP API contracts (ingestion, retrieval, validation, decision, NL query, health/ready)
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
