# Changelog

All notable changes to this project will be documented in this file.

Format follows a simple Keep a Changelog style. Versions will be introduced when releases begin.

## [Unreleased]

### Added

- Domain and database architecture (Phase 2):
  - Entity domain model (`Customer` … `AuditEvent`) with data classification
  - PostgreSQL schema design, relationships/ER diagram, indexing, audit model
  - Database test plan (constraints, duplicates, transactions, idempotency)
  - ADR-0002: PostgreSQL as system of record
- Documentation foundation: root guides (`README`, `AGENTS`, `CONTRIBUTING`, `DEVELOPMENT`, `ARCHITECTURE`, `TESTING`, `SECURITY`, `ROADMAP`, `CHANGELOG`)
- `docs/` tree with section READMEs and templates for features, agents, ADRs, and audits
