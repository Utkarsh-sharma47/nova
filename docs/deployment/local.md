# Local deployment

1. Copy `.env.example` to `.env`.
2. Replace the database password and `API_AUTH_TOKEN` placeholders (non-placeholder tokens required outside `APP_ENV=test`).
3. Optionally set `POSTGRES_PORT` / `API_PORT` if host ports 5432/8000 are busy.
4. Run `docker compose up --build`.
5. Check `/health` for liveness and `/ready` for PostgreSQL/storage readiness.

The Compose API service builds `DATABASE_URL` as
`postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@db:5432/$POSTGRES_DB`.
Do not point the API at a host `DATABASE_URL` with `127.0.0.1` — that breaks
in-container networking.

The API image runs as UID/GID 10001. Its entrypoint waits for PostgreSQL, runs
`alembic upgrade head`, then starts uvicorn. PostgreSQL and document files use
separate named volumes. Changing a migration already applied to a persistent
volume is unsupported; create a forward migration instead.

Automated smoke (build, health, ready, metrics, ingest, restart recovery):

```bash
./scripts/verify-compose.sh
```
