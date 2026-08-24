# Development

Local development guidance for Nova.

## Current status

**Phase 3:** FastAPI, SQLAlchemy/Alembic persistence, local document storage, and
digital PDF/text ingestion are implemented. Runtime AI agents and the UI are not.

## Prerequisites

- Python **3.12+**
- Docker (optional, for Compose Postgres)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Local checks

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
ruff check src tests
mypy
pytest -q
```

PostgreSQL integration tests run when `TEST_DATABASE_URL` is set. They reset the
named test database before applying migrations; never point it at shared data.

To run the service, populate `.env` (including `API_AUTH_TOKEN`) and use
`docker compose up --build`. The container entrypoint applies Alembic migrations.

## Repository layout

```text
.
├── src/nova/api/           # HTTP routes, DI, error handling
├── src/nova/application/   # Ingestion use case
├── src/nova/domain/        # Lifecycle policy and errors
├── src/nova/infrastructure/# Document processors and storage
├── src/nova/persistence/   # SQLAlchemy models and repositories
├── src/nova/contracts/     # Frozen Phase 2 Pydantic contracts
├── alembic/                # Production schema migrations
├── tests/                  # Unit, contract, API, integration, security checks
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

Use `.env.example` as a template. Never commit secrets. See [`docs/security/baseline.md`](docs/security/baseline.md).

## Related documents

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [TESTING.md](TESTING.md)
- [docs/architecture/technology-stack.md](docs/architecture/technology-stack.md)
- [docs/deployment/architecture.md](docs/deployment/architecture.md)
