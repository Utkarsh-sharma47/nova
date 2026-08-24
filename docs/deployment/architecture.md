# Deployment architecture

ADR: [0008](../decisions/0008-deployment.md). Philosophy: [philosophy.md](./philosophy.md).

## Part 1 topology

```text
┌────────────┐     ┌────────────┐     ┌────────────┐
│  web (UI)  │────▶│    api     │────▶│  postgres  │
│  (Phase 6) │     │  FastAPI   │     │            │
└────────────┘     └─────┬──────┘     └────────────┘
                         │
                   local volume
                   (document bytes)
```

Compose services: `api`, `db`, optional `web` (later).

## Phase 3 reality

- `api` image entrypoint: `alembic upgrade head` → `uvicorn nova.api.main:create_app --factory`
- Document bytes on named volume `nova_uploads`
- Healthchecks on Postgres and HTTP `/health`

## Configuration

```bash
DATABASE_URL=postgresql+asyncpg://nova:***@db:5432/nova
API_AUTH_TOKEN=
DOCUMENT_STORAGE_PATH=/app/data/uploads
LOG_LEVEL=INFO
LLM_PROVIDER=mock
```

## Part 2 extension

Add `worker` service consuming ingestion jobs; same image possible with different command.
