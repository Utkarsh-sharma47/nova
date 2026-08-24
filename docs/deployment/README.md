# Deployment

Deployment, release, and CI/CD documentation for Nova.

## Documents (Phase 1)

| Document | Status |
|----------|--------|
| [philosophy.md](./philosophy.md) | Done — simple Part 1 deploy stance |
| [ci-cd.md](./ci-cd.md) | Done — Phase 1 CI foundation and deferred checks |

## CI today

`.github/workflows/ci.yml` runs:

- `scripts/check-docs-structure.sh`
- `scripts/check-secret-patterns.sh`

No application lint/type/test/build jobs until a stack exists.

## Planned (implementation phases)

| Topic | Status |
|-------|--------|
| Environments (dev / staging / prod) | Planned |
| Language toolchain CI (lint/types/tests/build) | Phase 2+ |
| Configuration and secrets injection | Planned |
| Rollout and rollback | Planned |

## Related

- [DEVELOPMENT.md](../../DEVELOPMENT.md)
- [Operations](../operations/)
- [Security](../security/)
- [Roadmap](../roadmap/)
