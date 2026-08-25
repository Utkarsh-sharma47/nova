# Testing

| Doc | Purpose |
|-----|---------|
| [philosophy.md](./philosophy.md) | Goals |
| [contract-requirements.md](./contract-requirements.md) | Required suites |
| [router-decision.md](./router-decision.md) | Router safety + decision regression |

## Documents

| Document | Status |
|----------|--------|
| [philosophy.md](./philosophy.md) | Done |
| [test-strategy.md](./test-strategy.md) | Done — pyramid and layer ownership |
| [contract-testing.md](./contract-testing.md) | Done — agent/API contract surfaces |
| [failure-testing.md](./failure-testing.md) | Done — fail-safe catalog |
| [performance-testing.md](./performance-testing.md) | Done — latency/throughput/cost (no tooling yet) |
| [validator-evaluation.md](./validator-evaluation.md) | Done — Validator safety + eval suites |
| [pipeline-integration.md](./pipeline-integration.md) | Done — Phase 7 E2E pipeline suite |
| [query-api.md](./query-api.md) | Done — Phase 8 grounded query suite |
| [frontend.md](./frontend.md) | Done — Phase 9 Vitest ops UI suite |
## Current automated checks
- Docs structure script
- Secret pattern script
- pytest (contracts, documents, API, query, router decisions, pipeline)
- Ruff + MyPy on application packages
- Frontend: `npm test`, `npm run typecheck`, `npm run build`
## Planned / specified
| Topic | Status |
|-------|--------|
| Suite layout and naming | Phase 3+ |
| Fixture policy (clean/messy samples) | Phase 5+; Router decision fixtures **done** (`fixtures/evaluation/decision/`) |
| Contract test catalog | Phase 3–4 |
| Expanded CI gates | Progressive with toolchain |
| Database constraint / integrity tests | **Partial** — failsafe CHECK covered in `tests/router/test_decision_persistence.py`; full plan remains in database-test-plan |
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
