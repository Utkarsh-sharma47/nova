# CI/CD

## Current repository reality (Phase 3 ops)

FastAPI ops shell, Compose, Alembic bootstrap, observability, contract tests.

## CI jobs (enforced)

| Check | How | Fails build on error |
|-------|-----|----------------------|
| Docs structure | `scripts/check-docs-structure.sh` | Yes |
| Secret patterns | `scripts/check-secret-patterns.sh` | Yes |
| Dockerfile structure | `scripts/check-dockerfile.sh` | Yes |
| Ruff | `ruff check src tests` | Yes |
| MyPy | `mypy` | Yes |
| Pytest | `pytest -q -m "not ops"` | Yes |
| Dependency audit | `pip-audit` | Yes |
| Migration validation | `alembic upgrade head` vs Postgres service | Yes |
| Docker build | `docker build -t nova-api:ci .` | Yes |

Workflow: `.github/workflows/ci.yml`

No `|| true` masking. Compose full-stack smoke is available via `./scripts/verify-compose.sh` (not every-PR gated; see [TESTING.md](../../TESTING.md)).

## Local run

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
./scripts/check-dockerfile.sh
pip install -e ".[dev]"
ruff check src tests
mypy
pytest -q -m "not ops"
pip-audit
```
