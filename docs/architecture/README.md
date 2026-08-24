# Architecture

Detailed architecture notes for Nova. High-level overview also in [ARCHITECTURE.md](../../ARCHITECTURE.md).

## Documents (Phase 1)

| Document | Status |
|----------|--------|
| [principles.md](./principles.md) | Done |
| [high-level-overview.md](./high-level-overview.md) | Done — conceptual |
| [part2-extension-points.md](./part2-extension-points.md) | Done |
| [engineering-standards.md](./engineering-standards.md) | Done |

## Still planned (implementation phases)

| Topic | Status |
|-------|--------|
| Concrete context diagram with chosen stack | Phase 2 ADR |
| Storage and retention details | Phase 2–5 |
| External integrations | Phase 2+ / Part 2 |
| Failure/retry implementation specifics | Phase 3–4 |

## Rules

- Do not invent stack choices. Record them as ADRs in [`../decisions/`](../decisions/).
- Keep aligned with [`../agents/`](../agents/).
- When architecture changes, update ADRs and this section in the same PR.

## Related

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Decisions (ADRs)](../decisions/)
- [Agents](../agents/)
- [API](../api/)
- [Database](../database/)
