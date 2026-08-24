# Roadmap (detail)

Phase-level roadmap notes. Overview: [ROADMAP.md](../../ROADMAP.md).

## Phase 1 — Documentation foundation (current)

**Goal:** Establish a durable documentation architecture before application code.

**Deliverables:**

- Root guides: README, AGENTS, CONTRIBUTING, DEVELOPMENT, ARCHITECTURE, TESTING, SECURITY, ROADMAP, CHANGELOG
- `docs/` section READMEs
- Templates: feature, agent, ADR, audit

**Exit criteria:**

- Contributors and AI agents can find where each class of document belongs
- Agent operating rules are explicit in `AGENTS.md`
- No undecided technologies presented as fact

## Phase 2 — Requirements and product definition

**Goal:** Clarify problem, users, and acceptance criteria.

**Deliverables (planned):** requirements and product docs sufficient to drive ADRs.

## Phase 3 — Architecture decisions

**Goal:** Accept initial ADRs for orchestration, storage, APIs, and agent contracts.

## Phase 4 — Implementation skeleton

**Goal:** Bootstrap application structure, dev workflow, and test/evaluation harness foundations.

## Phase 5 — Core validation loop

**Goal:** End-to-end path from document intake to decision, including human review.

## Updating this roadmap

- Keep [ROADMAP.md](../../ROADMAP.md) and this directory synchronized.
- Prefer ADRs for technology choices; keep this file phase-oriented.
- Note slippage or scope cuts in [CHANGELOG.md](../../CHANGELOG.md) when significant.

## Related

- [Requirements](../requirements/)
- [Decisions](../decisions/)
- [Audits](../audits/)
