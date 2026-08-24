# Architecture Decision Records

ADRs record significant decisions. Use sequential IDs and the template.

| ID | Title | Status |
|----|-------|--------|
| [0001](./0001-documentation-first-phase1.md) | Documentation-first Phase 1 foundation | Accepted |
| [0002](./0002-ai-agent-contracts-and-trust-model.md) | AI agent contracts and trust model | Accepted |
| [0003](./0003-postgresql-persistence.md) | PostgreSQL as system of record | Accepted |

> **Integration note:** Specialist branches originally both used `0002`. During Phase 2 integration, PostgreSQL persistence is numbered **0003**. Stack ADRs from the architecture workstream will be renumbered to a coherent sequence (backend, database, API, AI provider, …) if needed.

## When to write an ADR

- Technology stack selection
- Agent contract shape changes
- Persistence technology choice
- Routing policy framework choice
- Part 2 interface changes that affect Part 1

## Creating an ADR

1. Copy [ADR_TEMPLATE.md](ADR_TEMPLATE.md).
2. Use the next numeric ID and a short slug filename.
3. Set status to Proposed → Accepted / Rejected / Superseded.
4. Link it from this README.
5. Update related architecture/requirements docs in the same PR.
6. When superseding, update both old and new ADRs.

## Related

- [ADR_TEMPLATE.md](ADR_TEMPLATE.md)
- [Architecture](../architecture/)
- [Database](../database/)
- [AGENTS.md](../../AGENTS.md)
