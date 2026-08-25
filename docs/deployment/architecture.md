# Deployment architecture

ADR: [0008](../decisions/0008-deployment.md). Philosophy: [philosophy.md](./philosophy.md). Local commands: [local.md](./local.md).

## Part 1 topology

```text
┌────────────┐     ┌────────────┐     ┌────────────┐
│  web (UI)  │────▶│    api     │────▶│  postgres  │
│  (Phase 6) │     │  FastAPI   │     │            │
└────────────┘     └─────┬──────┘     └────────────┘
                         │
                   object storage / volume
                   (document bytes — later)
```

Compose services for Part 1 now: **`api` + `db`**. No Kubernetes. No microservices split.

## Priorities

| Priority | How addressed |
|----------|---------------|
| Easy deployment | `docker compose up --build` |
| Low ops complexity | Two containers; entrypoint migrations |
| Reproducibility | Image build from `Dockerfile` + pinned dependency ranges |
| Environment config | `.env` / Compose `environment` |
| Health checks | Compose + image `HEALTHCHECK`; `/health`, `/ready` |
| Logs | JSON stdout |
| Persistent DB | named volume `nova_pg` |
| Startup ordering | `depends_on: db: condition: service_healthy` |
| Clean shutdown | `stop_grace_period: 30s`; `exec uvicorn` for SIGTERM |
| Restart | `restart: unless-stopped` |
| Rollback | Prior image tag; forward-compatible migrations |

## Configuration

See `.env.example`. Important variables:

Compose builds the API `DATABASE_URL` from `POSTGRES_*` and always targets hostname `db` (avoids leaking a host `localhost` URL into the container). Host-run API should set `DATABASE_URL` to `localhost` explicitly.

```bash
POSTGRES_USER=nova
POSTGRES_PASSWORD=nova
POSTGRES_DB=nova
ENVIRONMENT=local
LOG_LEVEL=INFO
LLM_PROVIDER=mock
```

Secrets only via env — never baked into the image.

## Container

`Dockerfile`: Python 3.12-slim multi-stage, non-root `nova` (UID 10001), `HEALTHCHECK` on `/health`, entrypoint runs migrations then `exec`s uvicorn.

## Migrations

Alembic (`alembic/`). Bootstrap revision `0001_schema_meta` creates `schema_meta` used by `/ready`. Full domain schema remains Phase 5.

## Part 2 extension

Add `worker` service consuming ingestion jobs; same image possible with different command. No redesign of api/db contracts.
