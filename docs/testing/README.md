# Testing

| Doc | Purpose |
|-----|---------|
| [philosophy.md](./philosophy.md) | Goals |
| [contract-requirements.md](./contract-requirements.md) | Required suites |

## Documents

| Document | Status |
|----------|--------|
| [philosophy.md](./philosophy.md) | Done |
| [test-strategy.md](./test-strategy.md) | Done — pyramid and layer ownership |
| [contract-testing.md](./contract-testing.md) | Done — agent/API contract surfaces |
| [failure-testing.md](./failure-testing.md) | Done — fail-safe catalog |
| [performance-testing.md](./performance-testing.md) | Done — latency/throughput/cost (no tooling yet) |
| [validator-evaluation.md](./validator-evaluation.md) | Done — Validator safety + eval suites |
| [query-api.md](./query-api.md) | Done — Phase 8 query/security/failure suites |
## Current automated checks
- Docs structure script
- Secret pattern script
No application test suite yet — do not invent fake app tests.
## Planned / specified
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
- [testing rules](../ai-development/testing-rules.md)
Root: [TESTING.md](../../TESTING.md).
