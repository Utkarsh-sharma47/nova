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
| [phase-10-system-verification.md](./phase-10-system-verification.md) | Done — Phase 10 33-case matrix + integrity |

## Current automated checks

- Docs structure script
- Secret pattern script
- pytest (contracts, documents, API, query, router, pipeline, e2e)
- `scripts/run_full_evaluation.py` AI gates
- Ruff + MyPy on application packages
- Frontend: `npm test`, `npm run typecheck`, `npm run build`

## Related

- [TESTING.md](../../TESTING.md)
- [Evaluation](../evaluation/)
- [CI/CD](../deployment/ci-cd.md)
- [AGENTS.md](../../AGENTS.md)

Root: [TESTING.md](../../TESTING.md).
