# Local deployment (Phase 3)

## Compose

```bash
cp .env.example .env
# set API_AUTH_TOKEN
docker compose up --build
```

Services:

| Service | Port | Notes |
|---------|------|-------|
| `db` | 5432 | Postgres 16, user/db `nova` / `nova` |
| `api` | 8000 | Migrates then serves FastAPI |

Endpoints: `GET /health`, `GET /ready`, `POST /v1/documents`.

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
