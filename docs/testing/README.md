# Testing

Detailed testing documentation for Nova. Overview: [TESTING.md](../../TESTING.md).

## Documents

| Document | Status |
|----------|--------|
| [philosophy.md](./philosophy.md) | Done |
| [test-strategy.md](./test-strategy.md) | Done — pyramid and layer ownership |
| [contract-testing.md](./contract-testing.md) | Done — agent/API contract surfaces |
| [failure-testing.md](./failure-testing.md) | Done — fail-safe catalog |
| [performance-testing.md](./performance-testing.md) | Done — latency/throughput/cost (no tooling yet) |

## Current automated checks

- Docs structure script
- Secret pattern script

No application test suite yet — do not invent fake app tests.

## Related

- [TESTING.md](../../TESTING.md)
- [Evaluation](../evaluation/)
- [CI/CD](../deployment/ci-cd.md)
- [AGENTS.md](../../AGENTS.md)
- [testing rules](../ai-development/testing-rules.md)
