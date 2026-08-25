# ADR-0001: Documentation-first Phase 1 foundation

- Status: Accepted
- Date: 2026-08-25

## Context

The Nova assignment requires a production-quality multi-agent trade-document verification system. The repository started empty aside from a README. Jumping straight into agent code would freeze accidental architecture, skip requirement traceability, and encourage prototype shortcuts.

## Decision

Phase 1 delivers **engineering foundation only**:

- Requirements inventory with stable IDs (assignment vs engineering)
- Product/problem/solution definitions
- Scope boundaries and Part 2 extension points
- Architecture principles and engineering standards
- Documentation system under `docs/`
- Git workflow and PR template
- AI agent governance (`AGENTS.md`)
- CI limited to checks applicable to a docs-only repository
- Security baseline for secrets hygiene

No application implementation, no fake app tests, no premature toolchain.

## Consequences

- Later phases can implement against explicit `REQ-*` IDs and contracts.
- CI remains honest until an application stack exists.
- Contributors and coding agents share one rule set.
- Part 2 needs are preserved as extension points without over-engineering.
