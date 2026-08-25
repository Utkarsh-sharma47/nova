# Testing

Testing strategy for Nova.

## Goals

- Protect extraction, validation, and decision contracts.
- Catch regressions in rule evaluation and agent behavior.
- Support honest reporting of quality (see also [docs/evaluation/](docs/evaluation/)).

## Current status

Phase 10 adds full-system verification on top of Phases 3–9: a 33-case E2E
matrix (`tests/e2e/`), unified AI evaluation gates, and CI frontend coverage.

```bash
pip install -e ".[dev]"
pytest -q
pytest -q tests/e2e/
python scripts/run_full_evaluation.py
cd frontend && npm test && npm run typecheck && npm run build
```

Detail: [`docs/testing/phase-10-system-verification.md`](docs/testing/phase-10-system-verification.md).

The default suite skips PostgreSQL migration verification unless
`TEST_DATABASE_URL` is set. With a disposable PostgreSQL database:

```bash
export TEST_DATABASE_URL=postgresql+psycopg://nova:nova@localhost:5432/nova_test
export DATABASE_URL="$TEST_DATABASE_URL"
pytest -q
```

The migration test downgrades that database to base and upgrades it twice.

Tooling: **pytest** (+ pytest-asyncio reserved), **Ruff**, **MyPy** ([ADR-0002](docs/decisions/0002-backend-stack.md));
frontend **Vitest** ([ADR-0009](docs/decisions/0009-frontend-stack.md)).

Required suites: [`docs/testing/contract-requirements.md`](docs/testing/contract-requirements.md).
Philosophy: [`docs/testing/philosophy.md`](docs/testing/philosophy.md).
Frontend: [`docs/testing/frontend.md`](docs/testing/frontend.md).

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
## Test layers
| Layer | Intent | Status |
|-------|--------|--------|
| Unit | Config, lifecycle, processors, storage | **Phase 3** |
| Integration | HTTP ingestion and PostgreSQL migrations | **Phase 3** |
| Contract | Stable schemas for agent I/O and APIs | **Phase 2** |
| End-to-end | Document in → decision out | Phase 6–7 |
| Evaluation | Accuracy on curated sets | Phase 5+ |
| Failure | DB-down readiness, corrupt and unsupported input | **Phase 3** |

## Expectations for contributors

- New behavior includes tests at the appropriate layer.
- Bug fixes include a regression test when feasible.
- Run relevant tests before claiming success.
- Do not fabricate test results. If tests cannot run, say so.

## Fixtures and data

- Prefer synthetic or anonymized documents.
- Never commit real customer PII or production documents.

## Related documents

- [docs/testing/](docs/testing/)
- [docs/evaluation/](docs/evaluation/)
- [AGENTS.md](AGENTS.md)
- [DEVELOPMENT.md](DEVELOPMENT.md)
