# Development

Local development guidance for Nova.

## Current status

**Phase 2:** Python contracts package exists. FastAPI app, agents, ORM, and UI are not implemented yet.

## Prerequisites

- Python **3.12+**
- Docker (optional, for Compose Postgres)
- Node **20+** (Phase 6 UI only)

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

## Repository layout (Phase 2)

```text
.
├── src/nova/contracts/     # Pydantic domain contracts
├── tests/contracts/        # Schema tests
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
