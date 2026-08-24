# Testing

Testing strategy for Nova.

## Goals

- Protect extraction, validation, and decision contracts.
- Catch regressions in rule evaluation and agent behavior.
- Support honest reporting of quality (see also [docs/evaluation/](docs/evaluation/)).

## Current status

No application test suite exists yet — and Phase 1 intentionally does **not** invent fake app tests.

Phase 1 automated checks:

- `./scripts/check-docs-structure.sh`
- `./scripts/check-secret-patterns.sh`

Testing philosophy: [`docs/testing/philosophy.md`](docs/testing/philosophy.md).

Full pyramid and layer ownership: [`docs/testing/test-strategy.md`](docs/testing/test-strategy.md).

## Test layers (planned)

| Layer | Intent |
|-------|--------|
| Unit | Pure functions, parsers, rule helpers, transformers |
| Contract | Stable schemas for agent I/O and external APIs |
| Integration | Agent boundaries, storage, API handlers |
| Failure | Timeouts, provider/DB/file faults, retry exhaustion (fail closed) |
| End-to-end | Document in → decision out for representative flows |
| Evaluation | Accuracy / quality on curated document sets (not a substitute for unit tests) |
| Regression (AI) | Fixed labeled set re-scored after prompt/model/policy changes |
| Performance | Latency, throughput, cost per document (benchmark jobs; calibrate targets later) |

Exact tooling will be recorded when chosen. Detail: [contract](docs/testing/contract-testing.md), [failure](docs/testing/failure-testing.md), [performance](docs/testing/performance-testing.md), [evaluation](docs/evaluation/evaluation-framework.md).

## Expectations for contributors

- New behavior includes tests at the appropriate layer.
- Bug fixes include a regression test when feasible.
- Run relevant tests before claiming success.
- Do not fabricate test results. If tests cannot run, say so.

## Fixtures and data

- Prefer synthetic or anonymized documents.
- Never commit real customer PII or production documents.
- Document fixture conventions under `docs/testing/` as they emerge.

## Related documents

- [docs/testing/](docs/testing/)
- [docs/evaluation/](docs/evaluation/)
- [AGENTS.md](AGENTS.md)
- [DEVELOPMENT.md](DEVELOPMENT.md)
