# Testing

Testing strategy for Nova.

## Goals

- Protect extraction, validation, and decision contracts.
- Catch regressions in rule evaluation and agent behavior.
- Verify operational foundation (config, health, migrations, Compose).
- Support honest reporting of quality (see also [docs/evaluation/](docs/evaluation/)).

## Current status

| Suite | Location | Default CI |
|-------|----------|------------|
| Contract/schema | `tests/contracts/` | Yes |
| Ops unit/API | `tests/ops/` (`not ops` marker) | Yes |
| Compose integration | `tests/ops/test_compose.py` (`ops` marker) | No (manual / `RUN_OPS_TESTS=1`) |

```bash
pip install -e ".[dev]"
pytest -q -m "not ops"
```

Optional Compose tests:

```bash
cp .env.example .env
RUN_OPS_TESTS=1 pytest -q -m ops
# or
./scripts/verify-compose.sh
```

Tooling: **pytest**, **Ruff**, **MyPy**, **pip-audit** ([ADR-0002](docs/decisions/0002-backend-stack.md)).

## What Compose verification covers

| Behavior | Covered by |
|----------|------------|
| Container startup | `verify-compose.sh` / `test_compose.py` |
| Database readiness | `/ready` after `db` healthy |
| API health | `GET /health` |
| API readiness | `GET /ready` (requires `schema_meta`) |
| Migration execution | API entrypoint `alembic upgrade head` + CI migration job |
| Restart behavior | `docker compose restart api` then re-check |
| Invalid configuration | `tests/ops/test_config.py` (unit) |

## What was / wasn't tested in default CI

**Tested in CI:** Ruff, MyPy, unit/API ops tests, contract tests, secret scan, Dockerfile structure, `pip-audit`, Docker **image build**, Alembic upgrade against service Postgres.

**Not run in default CI (impractical as always-on):** full `docker compose up` stack test (use `./scripts/verify-compose.sh` or `RUN_OPS_TESTS=1`). Documented and scripted, not gated on every PR unless enabled.

## Test layers

| Layer | Intent | Status |
|-------|--------|--------|
| Unit | Config, logging, pure helpers | **Phase 3 ops** |
| API | Health/ready/metrics via TestClient | **Phase 3 ops** |
| Contract | Agent/API schemas | **Phase 2** |
| Compose/ops | Startup, ready, restart | Script + optional pytest |
| Agent / E2E / Eval | Pipeline quality | Later phases |

## Expectations for contributors

- New behavior includes tests at the appropriate layer.
- Bug fixes include a regression test when feasible.
- Run relevant tests before claiming success.
- Do not fabricate test results. If tests cannot run, say so.

## Related documents

- [docs/testing/](docs/testing/)
- [docs/deployment/local.md](docs/deployment/local.md)
- [DEVELOPMENT.md](DEVELOPMENT.md)
