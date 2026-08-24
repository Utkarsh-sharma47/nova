# Deployment

Deployment and runtime release documentation for Nova.

## Purpose

Describe how the system is built, configured, released, and rolled back once a runtime exists.

## Current status

No deployment target or CI/CD pipeline has been decided. Do not invent cloud providers or orchestrators here.

## Planned contents

| Topic | Status |
|-------|--------|
| Environments (dev / staging / prod) | Planned |
| Build and release pipeline | Planned |
| Configuration and secrets | Planned |
| Rollout and rollback | Planned |

## Guidance

- Secrets never belong in git; document injection patterns when known.
- Link environment-specific runbooks from [`../operations/`](../operations/).
- Record major platform choices as ADRs.

## Related

- [DEVELOPMENT.md](../../DEVELOPMENT.md)
- [Operations](../operations/)
- [Security](../security/)
- [Roadmap](../roadmap/)
