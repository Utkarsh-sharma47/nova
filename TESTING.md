# Testing

Testing strategy for Nova.

## Goals

- Protect extraction, validation, and decision contracts.
- Catch regressions in rule evaluation and agent behavior.
- Support honest reporting of quality (see also [docs/evaluation/](docs/evaluation/)).

## Current status

**Phase 12** final Part 1 release verification (on top of Phases 3–11):

- Backend: pytest (unit, contract, API, pipeline, query, failure, evaluation)
- Frontend: Vitest + typecheck + production build
- Migrations: clean upgrade to `0004_phase7_pipeline` (CI + local)
- Compose smoke / recovery: `scripts/verify-production-readiness.sh`
- AI eval: `scripts/run_full_evaluation.py` (false AUTO_APPROVE = 0 gate)
- CI: docs/secrets, Ruff, MyPy, pytest, pip-audit, frontend checks, Docker builds

```bash
pip install -e ".[dev]"
pytest -q
cd frontend && npm test && npm run typecheck && npm run build
PYTHONPATH=src python scripts/run_full_evaluation.py
./scripts/verify-production-readiness.sh
```

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

## Test layers

| Layer | Intent | Status |
|-------|--------|--------|
| Unit | Config, lifecycle, processors, storage, agents | Implemented |
| Contract | Stable schemas for agent I/O and APIs | Implemented |
| Integration | HTTP ingestion, query, PostgreSQL migrations | Implemented |
| Failure | DB-down readiness, corrupt/unsupported input, fail-closed | Implemented |
| End-to-end | Document in → decision out + Phase 10 matrix | Implemented (`tests/pipeline/`, `tests/e2e/`) |
| Evaluation | Accuracy on curated sets; false AUTO_APPROVE = 0 | Implemented |
| Performance | Latency/cost benchmarks | Deferred / calibrate later |

## Expectations for contributors

- New behavior includes tests at the appropriate layer.
- Bug fixes include a regression test when feasible.
- Run relevant tests before claiming success.
- Do not fabricate test results. If tests cannot run, say so.
- Never mark remote deploy as PASS when status is **NOT EXECUTED**.

## Fixtures and data

- Prefer synthetic or anonymized documents.
- Never commit real customer PII or production documents.

## Related documents

- [docs/testing/](docs/testing/)
- [docs/evaluation/](docs/evaluation/)
- [docs/audits/phase-11-production-readiness.md](docs/audits/phase-11-production-readiness.md)
- [AGENTS.md](AGENTS.md)
- [DEVELOPMENT.md](DEVELOPMENT.md)
