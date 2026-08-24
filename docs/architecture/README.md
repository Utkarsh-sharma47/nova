# Architecture

| Document | Status |
|----------|--------|
| [principles.md](./principles.md) | Phase 1 |
| [high-level-overview.md](./high-level-overview.md) | Phase 2 |
| [system-architecture.md](./system-architecture.md) | Phase 2 |
| [layering.md](./layering.md) | Phase 2 |
| [ai-architecture.md](./ai-architecture.md) | Phase 2 |
| [technology-stack.md](./technology-stack.md) | Phase 2 |
| [contracts.md](./contracts.md) | Phase 2 |
| [error-model.md](./error-model.md) | Phase 2 |
| [confidence-and-evidence.md](./confidence-and-evidence.md) | Phase 2 |
| [lifecycle-and-idempotency.md](./lifecycle-and-idempotency.md) | Phase 2 |
| [part2-extension-points.md](./part2-extension-points.md) | Phase 1 |
| [engineering-standards.md](./engineering-standards.md) | Phase 1 |

## Contents / planned

| Topic | Status |
|-------|--------|
| Concrete context diagram with chosen stack | Phase 2 ADR |
| Storage and retention | **Domain/DB design documented** — see [`../database/`](../database/) |
| External integrations | Phase 2+ / Part 2 |
| Failure/retry implementation specifics | Phase 3–4 |
## Rules
- Do not invent stack choices. Record them as ADRs in [`../decisions/`](../decisions/).
- Keep aligned with [`../agents/`](../agents/) and [`../agents/contracts.md`](../agents/contracts.md).
- When architecture changes, update ADRs and this section in the same PR.
## Related
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Decisions (ADRs)](../decisions/)
- [Agents](../agents/)
- [Agent contracts](../agents/contracts.md)
- [API](../api/)
- [Database](../database/)
Related: [ARCHITECTURE.md](../../ARCHITECTURE.md), [ADRs](../decisions/), [Agents](../agents/), [API](../api/), [Database](../database/).
