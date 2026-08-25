# Local deployment (Docker Compose)

Exact commands for the Phase 3 operational foundation (ADR-0008).

## Prerequisites

- Docker Engine + Docker Compose v2+
- Git

## Bootstrap

```bash
git clone https://github.com/Utkarsh-sharma47/nova.git
cd nova
cp .env.example .env
docker compose up --build
```

Migrations run automatically in the API entrypoint (`alembic upgrade head`) after Postgres is healthy.

## Expected behavior

| Check | How | Expected |
|-------|-----|----------|
| Postgres healthy | `docker compose ps` | `db` healthy |
| API liveness | `curl -fsS http://127.0.0.1:8000/health` | `{"status":"ok",...}` |
| API readiness | `curl -fsS http://127.0.0.1:8000/ready` | `{"status":"ready",...}` after migrations |
| Metrics | `curl -fsS http://127.0.0.1:8000/metrics` | Prometheus text including `nova_http_*` |
| Logs | `docker compose logs -f api` | JSON lines with `timestamp`, `level`, `request_id`, `trace_id` |

## Manual migration (host)

If you run the API outside Compose:

```bash
export DATABASE_URL=postgresql+psycopg://nova:nova@localhost:5432/nova
alembic upgrade head
uvicorn nova.api.app:app --reload --port 8000
```

## Clean shutdown / restart

```bash
docker compose stop          # SIGTERM to containers; stop_grace_period=30s
docker compose start
docker compose restart api
docker compose down          # stop + remove containers
docker compose down -v       # also delete Postgres volume (destructive)
```

Compose uses `restart: unless-stopped` so containers come back after daemon restarts (unless explicitly stopped).

## End-to-end verify script

```bash
./scripts/verify-compose.sh
```

This builds, waits for `/health` and `/ready`, scrapes `/metrics`, restarts `api`, and confirms recovery.

## Invalid configuration

Missing or empty `DATABASE_URL` prevents API startup (Settings validation / entrypoint). Compose always injects a `db`-hosted URL from `POSTGRES_*`; invalid host Settings are covered by `tests/ops/test_config.py`.

```bash
# Entrypoint fails closed when DATABASE_URL is empty (no Compose injection)
docker compose run --rm --no-deps -e DATABASE_URL= api true
```

## Related

- [architecture.md](./architecture.md)
- [ci-cd.md](./ci-cd.md)
- [ADR-0008](../decisions/0008-deployment.md)
