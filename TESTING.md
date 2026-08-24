# Testing

Testing strategy for Nova.

## Goals

- Protect extraction, validation, and decision contracts.
- Catch regressions in ingestion, persistence, and API auth/idempotency.
- Support honest reporting of quality (see also [docs/evaluation/](docs/evaluation/)).

## Current status

Phase 3 suites:

| Suite | Path | Notes |
|-------|------|-------|
| Contracts | `tests/contracts/` | Phase 2 schemas |
| Config / domain / storage | `tests/config`, `tests/domain`, `tests/infrastructure` | Unit |
| API health/errors | `tests/api/test_health.py`, `test_errors.py` | Unit |
| Documents API | `tests/api/test_documents.py` | `@pytest.mark.integration` + Postgres |
| Repositories / migrations | `tests/persistence`, `tests/migrations` | Integration |

```bash
pip install -e ".[dev]"
export TEST_DATABASE_URL=postgresql+asyncpg://nova:nova@localhost:5432/nova_test
pytest -q
```

Tooling: **pytest** (+ pytest-asyncio), **Ruff**, **MyPy** ([ADR-0002](docs/decisions/0002-backend-stack.md)).

Required suites: [`docs/testing/contract-requirements.md`](docs/testing/contract-requirements.md).  
Philosophy: [`docs/testing/philosophy.md`](docs/testing/philosophy.md).

## Test layers

| Layer | Intent | Status |
|-------|--------|--------|
| Unit | Settings, lifecycle, storage safety, error envelope | **Phase 3** |
| Integration | API ingest + repos + Alembic | **Phase 3** (Postgres) |
| Contract | Agent/API schemas | **Phase 2** |
| End-to-end | Document in → decision out | Later |
| Evaluation | Accuracy on curated sets | Later |

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
