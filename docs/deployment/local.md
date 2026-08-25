# Local deployment (Phase 3)

## Compose

```bash
cp .env.example .env
# set API_AUTH_TOKEN
docker compose up --build
```

Optional host port overrides when defaults are busy:

```bash
POSTGRES_PORT=25432 API_PORT=28000 docker compose up --build
```

Services:

| Service | Port | Notes |
|---------|------|-------|
| `db` | `${POSTGRES_PORT:-5432}` | Postgres 16, user/db `nova` / `nova` |
| `api` | `${API_PORT:-8000}` | Migrates then serves FastAPI |

Endpoints: `GET /health`, `GET /ready`, `POST /v1/documents`.

**Intake behavior:** `POST /v1/documents` persists bytes + metadata and creates a
`verification_runs` row in `queued` status, then returns **202 Accepted**.
Phase 3 does **not** run Extractor/Validator/Router asynchronously after accept.

## Alembic only (host Python)

```bash
docker compose up -d db
export DATABASE_URL=postgresql+asyncpg://nova:nova@localhost:5432/nova
alembic upgrade head
```

## Test database

```bash
docker compose exec db createdb -U nova nova_test || true
export TEST_DATABASE_URL=postgresql+asyncpg://nova:nova@localhost:5432/nova_test
```
