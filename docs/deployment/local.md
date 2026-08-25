# Local deployment

1. Copy `.env.example` to `.env`.
2. Replace `POSTGRES_PASSWORD` and `API_AUTH_TOKEN` placeholders with real values (startup rejects known placeholders outside `APP_ENV=test`).
3. Optionally set `POSTGRES_PORT` / `API_PORT` / `WEB_PORT` if host ports are busy.
4. Run `docker compose up --build`.
5. Check `/health` (liveness) and `/ready` (PostgreSQL + schema + storage).
6. Open the ops UI at `http://localhost:8080` (Compose `web`).

Default host ports: API `8000`, UI `8080`, Postgres `5432`.

## Compose networking

The Compose API service builds `DATABASE_URL` as:

`postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@db:5432/$POSTGRES_DB`

Do not point the API at a host `DATABASE_URL` with `127.0.0.1` — that breaks in-container networking.

## Fresh local DB volume

Compose keeps Postgres data in the `nova_pg` named volume. Reset it when:

- switching from another Nova branch/worktree whose Alembic revisions differ (`Can't locate revision …`)
- changing `POSTGRES_PASSWORD` after the volume was already initialized

Disposable local reset only:

```bash
docker compose down -v
docker compose up --build
```

This destroys local DB + document volumes.

## Runtime-config injection (web)

Phase 11: the `web` service does **not** bake `API_AUTH_TOKEN` into the Vite build.

- Build arg: `VITE_API_BASE_URL=""` (same-origin `/v1` via nginx).
- Runtime env: `API_AUTH_TOKEN` → entrypoint writes `runtime-config.js` as `window.__NOVA_RUNTIME__`.
- Browser loads `/runtime-config.js` (Cache-Control: no-store) before using the API client.

Local Vite-only development still uses `frontend/.env` (`VITE_API_BASE_URL`, `VITE_API_AUTH_TOKEN`) against a host API.

## API container

The API image runs as UID/GID 10001. Entrypoint waits for PostgreSQL, runs `alembic upgrade head`, then starts uvicorn. PostgreSQL and document files use separate named volumes. Changing a migration already applied to a persistent volume is unsupported; create a forward migration instead. Production must not use `create_all`.

## Smoke / recovery

```bash
./scripts/verify-production-readiness.sh
```

Defaults: `API_PORT=18000`, `WEB_PORT=18080`, `POSTGRES_PORT=15432`.

Frontend-only notes: [`frontend.md`](./frontend.md). UI demo: [`../operations/ui-demo.md`](../operations/ui-demo.md). Recovery: [`../operations/recovery.md`](../operations/recovery.md).
