# Recovery runbook

Short procedures for Compose Part 1. Prefer restart-and-verify over ad-hoc schema edits. Full production procedure: [`../deployment/production.md`](../deployment/production.md).

## Prerequisites

```bash
cp .env.example .env   # if needed; non-placeholder secrets
docker compose ps
```

Automated smoke (health/ready/metrics + restart recovery + Alembic head):

```bash
./scripts/verify-production-readiness.sh
```

## API restart

```bash
docker compose restart api
docker compose ps api
curl -sf "http://localhost:${API_PORT:-8000}/health"
curl -sf "http://localhost:${API_PORT:-8000}/ready"
```

Entrypoint re-runs DB wait + `alembic upgrade head` (no-op when already at head) before uvicorn.

## Database restart

```bash
docker compose restart db
# wait until healthy
docker compose ps db
curl -sf "http://localhost:${API_PORT:-8000}/ready"
```

If `/ready` fails while Postgres is up, check API logs for connect timeouts (`DATABASE_CONNECT_TIMEOUT_SECONDS`) and that the volume `nova_pg` is intact.

## Web (UI) restart

```bash
docker compose restart web
curl -sf "http://localhost:${WEB_PORT:-8080}/" >/dev/null
# Confirm runtime config exists without printing the token:
curl -sf "http://localhost:${WEB_PORT:-8080}/runtime-config.js" | grep -q '__NOVA_RUNTIME__'
```

Restart regenerates `runtime-config.js` from the current `API_AUTH_TOKEN` env.

## Full stack restart

```bash
docker compose restart
# or
docker compose up -d --force-recreate
```

Order on cold start: `db` healthy → `api` healthy → `web`.

## Failed migration

Symptoms: API container exits during entrypoint; logs show Alembic error.

1. Capture logs: `docker compose logs api` (redact secrets).
2. Do **not** hand-edit `alembic_version` on a shared production volume.
3. For **disposable** local volumes only: `docker compose down -v` then `up --build` (destroys DB + document volumes).
4. For retained data: restore from backup, or apply a **forward** fix migration after root-causing the failure.
5. Confirm: `docker compose exec api alembic current` → `0004_phase7_pipeline`.

Production must not fall back to `create_all`.

## Temporary database outage

1. Stop or pause `db` (or block network) → `/ready` must fail; `/health` may still pass (liveness).
2. Restore `db` to healthy.
3. Restart `api` if the process exited; otherwise wait for pool recovery (`pool_pre_ping`).
4. Re-check `/ready` and a simple authenticated read.

## Verify script expectations

`scripts/verify-production-readiness.sh` (defaults `API_PORT=18000`, `WEB_PORT=18080`, `POSTGRES_PORT=15432`):

- Compose up with health/ready/metrics checks
- Runtime-config present without printing token values
- API / DB / web restart recovery
- `alembic current` contains `0004_phase7_pipeline`

## Related

- [`README.md`](./README.md)
- [`../deployment/local.md`](../deployment/local.md)
- [`../observability/architecture.md`](../observability/architecture.md)
