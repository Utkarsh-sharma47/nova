# Requirements

Source of truth for *what* Nova must do, independent of implementation.

## Documents (Phase 1)

| Document | Status |
|----------|--------|
| [inventory.md](./inventory.md) | Done — stable `REQ-*` IDs |
| [acceptance-criteria.md](./acceptance-criteria.md) | Done — Part 1 acceptance checklist |
| [traceability.md](./traceability.md) | Done — REQ → design → test → evidence |
| [scope-boundaries.md](./scope-boundaries.md) | Done — in/out of scope |

## Guidance

- Distinguish **ASSIGNMENT** vs **ENGINEERING** requirements in the inventory.
- Separate must-have (P0) from later (P1/P2).
- Reference product workflows in [`../product/`](../product/) rather than duplicating UI narrative.
- When a requirement drives an architectural choice, link the ADR in [`../decisions/`](../decisions/).

## Related

- [Product](../product/)
- [Roadmap](../roadmap/)
- Root [ROADMAP.md](../../ROADMAP.md)
