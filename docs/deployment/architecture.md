# Deployment architecture

ADR: [0008](../decisions/0008-deployment.md). Philosophy: [philosophy.md](./philosophy.md).

## Part 1 topology (Phase 11)

```text
┌────────────────────┐     ┌────────────────────┐     ┌────────────┐
│  web (ops UI)      │────▶│  api (FastAPI)     │────▶│  postgres  │
│  nginx-unprivileged│     │  non-root UID 10001│     │  16-alpine  │
│  :8080             │     │  :8000             │     │  :5432      │
└─────────┬──────────┘     └─────────┬──────────┘     └────────────┘
          │                          │
   runtime-config.js          document volume
   (API_AUTH_TOKEN at start)  /var/lib/nova/documents
```

Compose services: **`api`**, **`db`**, **`web`**.

| Service | Image role | Notes |
|---------|------------|-------|
| `db` | `postgres:16-alpine` | Named volume `nova_pg`; healthcheck `pg_isready` |
| `api` | Multi-stage Python 3.12 slim | Runs as UID/GID **10001** (`nova`); entrypoint waits for DB, runs `alembic upgrade head`, then uvicorn |
| `web` | Multi-stage Node build → **nginxinc/nginx-unprivileged** | Listens on **8080**; proxies `/v1`, `/health`, `/ready`, `/metrics` to `api` |

## Non-root containers

- **API:** `USER nova` (10001). Document storage directory owned by that user.
- **Web:** `nginx-unprivileged` image; process runs as `nginx`, not root.
- **DB:** Official Postgres image defaults (acceptable for Part 1 Compose).

## Runtime secrets for web (no bake)

Auth tokens are **not** build-args for the web image.

1. Compose passes `API_AUTH_TOKEN` as a **runtime** environment variable to `web`.
2. `frontend/docker-entrypoint.sh` writes `/usr/share/nginx/html/runtime-config.js` at container start:

```javascript
window.__NOVA_RUNTIME__ = {
  apiBaseUrl: "",
  apiAuthToken: "<from env>"
};
```

3. The SPA reads `window.__NOVA_RUNTIME__` (see [`../architecture/frontend.md`](../architecture/frontend.md)). Build-time `VITE_API_AUTH_TOKEN` is for local Vite demos only.

Image layers therefore do not contain production API tokens.

## Configuration

Environment-only secrets and tunables. Full reference: [configuration.md](./configuration.md).

Compose builds `DATABASE_URL` as `postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@db:5432/$POSTGRES_DB`. Do not inject a host `DATABASE_URL` with `127.0.0.1` into the API container.

## Health and signals

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness |
| `GET /ready` | PostgreSQL + required schema + storage |
| `GET /metrics` | Prometheus exposition |

API uses `STOPSIGNAL SIGTERM` with uvicorn graceful shutdown; web uses `SIGQUIT` for nginx.

## Schema bootstrap

Production and Compose use **Alembic only**. Application startup must **not** call SQLAlchemy `MetaData.create_all` against the live database. `create_all` appears only in test fixtures.

Head revision for Part 1 pipeline schema: `0004_phase7_pipeline`.

## Part 2 extension

Add a `worker` service consuming ingestion jobs; same API image with a different command is acceptable. Do not redesign `api`/`db` contracts.

## Related

- [local.md](./local.md) · [frontend.md](./frontend.md) · [production.md](./production.md)
- [../operations/recovery.md](../operations/recovery.md)
- [../security/architecture.md](../security/architecture.md)
