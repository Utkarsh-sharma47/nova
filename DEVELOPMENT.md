# Development

Local development guidance for Nova.

## Current status

**Phase 11:** Production hardening for the Part 1 stack — Compose (api + db + web), non-root containers, runtime web auth injection (`window.__NOVA_RUNTIME__`), request limits, observability (health/ready/metrics + JSON logs), and recovery docs. Application architecture is unchanged from Phases 7–9.

Remote deploy remains **NOT EXECUTED**. See [`docs/deployment/production.md`](docs/deployment/production.md).

## Prerequisites

- Python **3.12+**
- Node.js **20+** (frontend; CI uses 22)
- Docker (Compose Postgres + full stack)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

cd frontend
cp .env.example .env
npm install
```

Align `API_AUTH_TOKEN` (root `.env`) with `VITE_API_AUTH_TOKEN` (frontend `.env`) for Vite-only demos. Compose `web` injects the token at runtime instead of baking it.

## Local checks

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
ruff check src tests
mypy
pytest -q
cd frontend && npm test && npm run typecheck && npm run build
./scripts/verify-production-readiness.sh
```

PostgreSQL integration tests run when `TEST_DATABASE_URL` is set. They reset the
named test database before applying migrations; never point it at shared data.

## Run the stack

```bash
docker compose up --build
# API http://localhost:8000  ·  UI http://localhost:8080
```

Or API via Compose/uvicorn and UI via Vite:

```bash
cd frontend && npm run dev
```

## Production-readiness verify script

```bash
./scripts/verify-production-readiness.sh
```

Uses `API_PORT=18000`, `WEB_PORT=18080`, `POSTGRES_PORT=15432` by default. Checks health/ready/metrics, runtime-config (without printing the token), API/DB/web restart recovery, and `alembic current` for `0004_phase7_pipeline`.

## Repository layout

```text
.
├── frontend/               # React + TypeScript + Vite ops UI
├── src/nova/api/           # HTTP routes, DI, error handling
├── src/nova/application/   # Ingestion, pipeline, ops reads
├── src/nova/query/         # Grounded NL query service
├── src/nova/domain/        # Lifecycle policy and errors
├── src/nova/infrastructure/# Document processors and storage
├── src/nova/persistence/   # SQLAlchemy models and repositories
├── src/nova/contracts/     # Pydantic contracts
├── alembic/                # Production schema migrations
├── tests/                  # Unit, contract, API, integration
├── fixtures/demo/          # Synthetic UI demo fixtures
├── docs/                   # Architecture, ADRs, requirements
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── scripts/
```

## Branching

Follow [`docs/operations/git-workflow.md`](docs/operations/git-workflow.md):

- Branch from latest `main`
- Prefixes: `feature/`, `fix/`, `docs/`, `test/`, `chore/`
- Never push directly to `main`

## Environment configuration

Use `.env.example` and `frontend/.env.example` as templates. Never commit secrets.
Full reference: [`docs/deployment/configuration.md`](docs/deployment/configuration.md).
See [`docs/security/baseline.md`](docs/security/baseline.md).

## Related documents

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [TESTING.md](TESTING.md)
- [docs/architecture/frontend.md](docs/architecture/frontend.md)
- [docs/deployment/frontend.md](docs/deployment/frontend.md)
- [docs/operations/ui-demo.md](docs/operations/ui-demo.md)
- [docs/operations/recovery.md](docs/operations/recovery.md)
- [docs/audits/phase-11-production-readiness.md](docs/audits/phase-11-production-readiness.md)
