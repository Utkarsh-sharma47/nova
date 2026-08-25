# CI/CD

Workflow: [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml).

Phase 11 keeps CI deterministic on GitHub-hosted runners: no live vendor LLM keys, disposable Postgres service container, and image builds without pushing secrets.

## Jobs

### `foundation-checks` — Docs and secrets

| Step | Command |
|------|---------|
| Docs structure | `./scripts/check-docs-structure.sh` |
| Secret patterns | `./scripts/check-secret-patterns.sh` |

### `python` — Ruff, MyPy, pytest, migrations, audits, API image

| Step | What |
|------|------|
| Ruff | `ruff check src tests` |
| MyPy | `mypy` |
| Tests | `pytest -q` with Postgres service (`APP_ENV=test`) |
| Migrations | `alembic downgrade base` → `upgrade head` ×2; assert `0004_phase7_pipeline`; required tables present |
| Dependency audit | `pip-audit` (findings reported; does not silently invent clean bills) |
| Docker | `docker build -t nova-api:ci .` |

### `frontend` — Typecheck, test, build, audit, web image

| Step | What |
|------|------|
| Install | `npm ci` |
| Typecheck | `npm run typecheck` |
| Test | `npm test` (Vitest) |
| Build | `npm run build` with empty `VITE_API_BASE_URL` (same-origin) — **no auth token env in CI build** |
| npm audit | `npm audit --audit-level=high` |
| Docker | `docker build -t nova-web:ci ./frontend` |

## Local parity

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
pip install -e ".[dev]"
ruff check src tests
mypy
pytest -q
cd frontend && npm ci && npm run typecheck && npm test && npm run build
docker build -t nova-api:local .
docker build -t nova-web:local ./frontend
./scripts/verify-production-readiness.sh
```

## Deployment workflow

CI **builds** images; it does **not** deploy to a remote environment.

Operator deploy path: [production.md](./production.md). **Remote deploy: NOT EXECUTED** in Phase 11.

## Related

- [architecture.md](./architecture.md)
- [../audits/phase-11-production-readiness.md](../audits/phase-11-production-readiness.md)
