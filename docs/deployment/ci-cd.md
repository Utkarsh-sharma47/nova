# CI/CD

## Current repository reality (Phase 3)

Docs + contracts + FastAPI ingestion backend. CI runs lint, typecheck, pytest (with Postgres service), and Docker build.

## CI jobs (enforced)

| Check | How |
|-------|-----|
| Docs structure | `scripts/check-docs-structure.sh` |
| Secret patterns | `scripts/check-secret-patterns.sh` |
| Ruff | `ruff check src tests` |
| MyPy | `mypy` |
| Alembic | `alembic upgrade head` against service Postgres |
| Pytest | `pytest -q` (`TEST_DATABASE_URL`) |
| Docker | `docker build -t nova-api:ci .` |

Workflow: `.github/workflows/ci.yml`

## Local run

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
pip install -e ".[dev]"
ruff check src tests
mypy
alembic upgrade head
pytest -q
```
