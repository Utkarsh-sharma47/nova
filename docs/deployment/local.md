# Local deployment

1. Copy `.env.example` to `.env`.
2. Replace the database password and `API_AUTH_TOKEN` placeholders (non-placeholder tokens required outside `APP_ENV=test`).
3. Optionally set `POSTGRES_PORT` / `API_PORT` / `WEB_PORT` if host ports are busy.
4. Run `docker compose up --build`.
5. Check `/health` for liveness and `/ready` for PostgreSQL/storage readiness.
6. Open the ops UI at `http://localhost:8080` (Compose `web` service).

The Compose API service builds `DATABASE_URL` as
`postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@db:5432/$POSTGRES_DB`.
Do not point the API at a host `DATABASE_URL` with `127.0.0.1` — that breaks
in-container networking.

The `web` service builds the Vite app with empty `VITE_API_BASE_URL` so the
browser calls same-origin `/v1/*`, which nginx proxies to `api`.

The API image runs as UID/GID 10001. Its entrypoint waits for PostgreSQL, runs
`alembic upgrade head`, then starts uvicorn. PostgreSQL and document files use
separate named volumes. Changing a migration already applied to a persistent
volume is unsupported; create a forward migration instead.

Frontend-only local notes: [`frontend.md`](./frontend.md). UI demo: [`../operations/ui-demo.md`](../operations/ui-demo.md).
