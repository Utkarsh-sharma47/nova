# CI/CD

## Current repository reality (Phase 2)

Documentation + governance + **Pydantic domain contracts**. No FastAPI routes, agents, ORM, or UI yet.

## CI jobs (enforced)

| Check | How |
|-------|-----|
| Docs structure | `scripts/check-docs-structure.sh` |
| Secret patterns | `scripts/check-secret-patterns.sh` |
| Ruff | `ruff check src tests` |
| MyPy | `mypy` |
| Contract tests | `pytest -q` |

Workflow: `.github/workflows/ci.yml`

## Local run

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
pip install -e ".[dev]"
ruff check src tests
mypy
pytest -q
```
