# Roadmap

Phased delivery plan for Nova. Detailed phase notes live in [`docs/roadmap/`](docs/roadmap/).

## Phase 1 — Documentation foundation (current)

- Establish documentation architecture under `docs/`
- Define agent operating rules ([AGENTS.md](AGENTS.md))
- Templates for features, agents, ADRs, and audits
- Root contributor and architecture overviews

## Phase 2 — Requirements and product definition

- Problem statements and acceptance criteria
- Personas and primary user workflows
- Non-goals and constraints

## Phase 3 — Architecture decisions

- Record ADRs for orchestration, storage, APIs, and agent contracts
- **Done (docs):** PostgreSQL system of record + domain/schema design ([ADR-0002](docs/decisions/0002-postgresql-persistence.md), [`docs/database/`](docs/database/))
- Freeze initial interfaces for extraction, validation, and decisioning

## Phase 4 — Implementation skeleton

- Application bootstrap and development workflow
- Initial agent pipeline scaffolding
- Test and evaluation harness foundations

## Phase 5 — Core validation loop

- Document intake → extraction → rules → decision
- Human review path
- Observability for decisions

## Later phases

Subsequent phases (customer rule configuration, scale, advanced evaluation, and operations hardening) will be defined as earlier phases complete. Avoid committing to technologies here until ADRs exist.

## Change policy

Roadmap updates should be reflected in both this file and `docs/roadmap/`. Significant scope changes deserve a short note in [CHANGELOG.md](CHANGELOG.md).
