# Testing

Detailed testing documentation for Nova. Overview: [TESTING.md](../../TESTING.md).

## Documents (Phase 1)

| Document | Status |
|----------|--------|
| [philosophy.md](./philosophy.md) | Done |

## Current automated checks

- Docs structure script
- Secret pattern script

No application test suite yet — do not invent fake app tests.

## Planned contents

| Topic | Status |
|-------|--------|
| Suite layout and naming | Phase 3+ |
| Fixture policy (clean/messy samples) | Phase 5 |
| Contract test catalog | Phase 3–4 |
| Expanded CI gates | Progressive with toolchain |
| Database constraint / integrity tests | **Specified** — [`../database/database-test-plan.md`](../database/database-test-plan.md) (not implemented yet) |

## Principles

- Tests must be runnable and honest; never fabricate results.
- Prefer deterministic fixtures; isolate flaky model-dependent checks under evaluation where appropriate.
- Document how to run each suite in [DEVELOPMENT.md](../../DEVELOPMENT.md) when commands exist.

## Related

- [TESTING.md](../../TESTING.md)
- [Evaluation](../evaluation/)
- [CI/CD](../deployment/ci-cd.md)
- [AGENTS.md](../../AGENTS.md)
- [Database test plan](../database/database-test-plan.md)
