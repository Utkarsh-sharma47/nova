# Development

Local development guidance for Nova.

## Current status

**Phase 3:** FastAPI API with document ingestion, PostgreSQL persistence (Alembic), and local filesystem storage. Agents / LLM calls are not implemented yet.

## Prerequisites

- Python **3.12+**
- Docker (Postgres 16 via Compose)
- Node **20+** (Phase 6 UI only)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# edit .env — set API_AUTH_TOKEN and DATABASE_URL
docker compose up -d db
alembic upgrade head
```

## Run the API

```bash
uvicorn nova.api.main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

Auth: `Authorization: Bearer <API_AUTH_TOKEN>` or `X-API-Key: <API_AUTH_TOKEN>` on `/v1/*`.  
Health: `GET /health`, `GET /ready` (no auth).

## Local checks

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
ruff check src tests
mypy
pytest -q
```

For integration tests, ensure `nova_test` exists:

```bash
docker compose exec db createdb -U nova nova_test || true
export TEST_DATABASE_URL=postgresql+asyncpg://nova:nova@localhost:5432/nova_test
pytest -q
```

## Repository layout (Phase 3)

```text
.
├── alembic/                  # Migrations
├── src/nova/
│   ├── api/                  # FastAPI app, routes, deps
│   ├── config/               # Settings
│   ├── contracts/            # Phase 2 Pydantic contracts (frozen)
│   ├── domain/               # Lifecycle + app errors
│   ├── infrastructure/       # Document storage
│   ├── observability/        # Structured logging
│   ├── persistence/          # ORM, DB, repositories
│   └── services/             # DocumentIngestionService
├── tests/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Branching

Follow [`docs/operations/git-workflow.md`](docs/operations/git-workflow.md):

- Branch from latest `main`
- Prefixes: `feature/`, `fix/`, `docs/`, `test/`, `chore/`
- Never push directly to `main`

## Environment configuration

Use `.env.example` as a template. Never commit secrets. See [`docs/security/baseline.md`](docs/security/baseline.md).

## Related documents

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [TESTING.md](TESTING.md)
- [docs/deployment/](docs/deployment/)
- [docs/database/](docs/database/)
