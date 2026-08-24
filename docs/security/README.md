# Security (detail)

Detailed security documentation. Overview: [SECURITY.md](../../SECURITY.md).

## Documents (Phase 1)

| Document | Status |
|----------|--------|
| [baseline.md](./baseline.md) | Done — secrets, logging, dependency pinning, deferred upload security |

## Still planned

| Topic | Status |
|-------|--------|
| Data classification | Planned |
| Threat model | Planned |
| Access control model | Planned |
| Document retention and deletion | Planned |
| Upload security controls | Implementation phases (`REQ-SEC-004`) |

## Guidance

- Assume document contents are sensitive.
- Prefer human review when policy or confidence is unclear.
- Coordinate with [`../observability/`](../observability/) on redaction.

## Related

- [SECURITY.md](../../SECURITY.md)
- [Operations](../operations/)
- [Audits](../audits/)
