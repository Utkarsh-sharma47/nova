# Decisions (ADRs)

Architecture Decision Records for Nova.

## Purpose

ADRs capture significant, lasting choices: orchestration, storage, APIs, agent contracts, evaluation approach, and similar. Prefer an ADR over scattering rationale across chat or PRs only.

## Process

1. Copy [ADR_TEMPLATE.md](ADR_TEMPLATE.md).
2. Name files `NNNN-short-title.md` with a monotonic number (start at `0001`).
3. Set status to Proposed → Accepted / Rejected / Superseded.
4. Link accepted ADRs from [`../architecture/`](../architecture/) when they affect system design.
5. When superseding, update both old and new ADRs.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0002](./0002-postgresql-persistence.md) | PostgreSQL as system of record | Accepted |

Note: ADR-0001 may be allocated by the Phase 1 documentation-foundation workstream. This branch records the persistence decision as **0002** to avoid ID collision.

## Related

- [ADR_TEMPLATE.md](ADR_TEMPLATE.md)
- [Architecture](../architecture/)
- [Database](../database/)
- [AGENTS.md](../../AGENTS.md)
