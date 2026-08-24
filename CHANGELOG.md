# Changelog

All notable changes to this project will be documented in this file.

Format follows a simple Keep a Changelog style. Versions will be introduced when releases begin.

## [Unreleased]

### Added

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
