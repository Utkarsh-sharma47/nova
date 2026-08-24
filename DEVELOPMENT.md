# Development

Local development guidance for Nova.

## Current status

**Phase 3 operational foundation:** FastAPI API shell, Docker Compose (API + Postgres), Alembic bootstrap migration, structured logging, Prometheus metrics, health/readiness.

Agent business logic (Extractor/Validator/Router) is **not** implemented yet.

## Prerequisites

- Python **3.12+**
- Docker Engine + Compose v2+
- Node **20+** (Phase 6 UI only)

## Recommended path (Compose)

```bash
git clone https://github.com/Utkarsh-sharma47/nova.git
cd nova
cp .env.example .env
docker compose up --build
# migrations run in the API entrypoint
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/ready
```

Full verify (build, ready, metrics, restart):

```bash
./scripts/verify-compose.sh
```

Details: [`docs/deployment/local.md`](docs/deployment/local.md).

## Host Python path (optional)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Point DATABASE_URL at Compose Postgres on localhost:
# DATABASE_URL=postgresql+psycopg://nova:nova@localhost:5432/nova
docker compose up -d db
export DATABASE_URL=postgresql+psycopg://nova:nova@localhost:5432/nova
alembic upgrade head
uvicorn nova.api.app:app --reload --port 8000
```

## Local checks

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
./scripts/check-dockerfile.sh
ruff check src tests
mypy
pytest -q -m "not ops"
pip-audit
```

Compose ops tests (optional, slow):

```bash
RUN_OPS_TESTS=1 pytest -q -m ops
```

## Repository layout (ops foundation)

```text
.
├── src/nova/
│   ├── api/                 # FastAPI app + /health /ready /metrics
│   ├── config.py            # pydantic-settings
│   ├── contracts/           # Phase 2 domain contracts
│   ├── db/                  # SQLAlchemy engine + schema_meta
│   └── observability/       # JSON logs, IDs, Prometheus metrics
├── alembic/                 # Migrations
├── tests/contracts/         # Schema tests
├── tests/ops/               # Config, logging, API, optional Compose
├── Dockerfile
├── docker-compose.yml
└── scripts/
```

## Branching

Follow [`docs/operations/git-workflow.md`](docs/operations/git-workflow.md). Never push directly to `main`.

## Related documents

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [TESTING.md](TESTING.md)
- [docs/deployment/](docs/deployment/)
- [docs/observability/](docs/observability/)
