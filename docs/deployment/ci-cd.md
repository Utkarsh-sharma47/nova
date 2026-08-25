# CI/CD

## Enforced GitHub Actions (`.github/workflows/ci.yml`)

| Job | Checks |
|-----|--------|
| Docs and secrets | `scripts/check-docs-structure.sh`, `scripts/check-secret-patterns.sh` |
| Python | Ruff, MyPy, pytest (Postgres service), `scripts/run_full_evaluation.py`, Alembic upgrade×2 to `0004_phase7_pipeline`, API `docker build` |
| Frontend | `npm ci`, typecheck, Vitest, production build |

Triggers: `pull_request` and `push` to `main`.

CI is deterministic: MockLLM / unit fixtures; Postgres for migration + integration
tests that use `TEST_DATABASE_URL`. No live vendor LLM calls.

## Local parity

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
pip install -e ".[dev]"
ruff check src tests
mypy
pytest -q
python scripts/run_full_evaluation.py
cd frontend && npm ci && npm run typecheck && npm test && npm run build
```

## Related

- [TESTING.md](../../TESTING.md)
- [phase-10-system-verification.md](../testing/phase-10-system-verification.md)
- [phase-10-audit.md](../audits/phase-10-audit.md)
