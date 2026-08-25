# Development

Local development guidance for Nova.

## Current status

**Phase 9:** Part 1 React operations UI plus grounded query API on the Phase 7
pipeline. FastAPI, SQLAlchemy/Alembic, local document storage, and PDF/text
ingestion remain the backend foundation.

## Prerequisites

- Python **3.12+**
- Node.js **20+** (frontend)
- Docker (optional, for Compose Postgres + full stack)

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

Align `API_AUTH_TOKEN` (root `.env`) with `VITE_API_AUTH_TOKEN` (frontend `.env`).

## Local checks

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
ruff check src tests
mypy
pytest -q
cd frontend && npm test && npm run typecheck && npm run build
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
See [`docs/security/baseline.md`](docs/security/baseline.md).

## Related documents

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [TESTING.md](TESTING.md)
- [docs/architecture/frontend.md](docs/architecture/frontend.md)
- [docs/deployment/frontend.md](docs/deployment/frontend.md)
- [docs/operations/ui-demo.md](docs/operations/ui-demo.md)
