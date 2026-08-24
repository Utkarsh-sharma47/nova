# Architecture

Detailed architecture notes for Nova. For the high-level overview, see [ARCHITECTURE.md](../../ARCHITECTURE.md).

## Scope

Document system boundaries, component responsibilities, data flows, and integration points as they are decided.

## Contents

| Topic | Status |
|-------|--------|
| Context diagram | Planned |
| Pipeline / agent orchestration | Planned |
| Storage and retention | **Domain/DB design documented** — see [`../database/`](../database/) and [ADR-0002](../decisions/0002-postgresql-persistence.md) |
| External integrations | Planned |
| Failure and retry strategy | Planned |

## Rules

- Do not invent stack choices. Record them as ADRs in [`../decisions/`](../decisions/).
- Keep this section aligned with agent docs in [`../agents/`](../agents/).
- When architecture changes, update ADRs and this section in the same PR.

## Related

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Decisions (ADRs)](../decisions/)
- [Agents](../agents/)
- [API](../api/)
- [Database](../database/)
