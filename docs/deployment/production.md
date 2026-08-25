# Production deployment runbook

Part 1 production path is **Docker Compose** on a single host (ADR-0008). No Kubernetes.

## Status

| Item | Status |
|------|--------|
| Local Compose procedure | Documented |
| Production config gates | Documented (`APP_ENV=production`) |
| Remote / cloud deploy | **NOT EXECUTED** |

Do not claim production availability until a real remote deploy is executed and recorded in the Phase 11 audit. This document is the procedure; it is not evidence of a live deployment.

## 1. Build

```bash
cp .env.example .env
# Set strong POSTGRES_PASSWORD and API_AUTH_TOKEN (≥24 chars for production)
# Set APP_ENV=production and tighten CORS_ORIGINS to real UI origins
# Set LLM_* if not using MockLLM

docker compose build
```

Images:

- **api** — Python 3.12 slim, non-root, Alembic entrypoint
- **web** — Vite build → nginx-unprivileged; **no auth token build-arg**
- **db** — `postgres:16-alpine`

## 2. Configuration

See [configuration.md](./configuration.md). Minimum production checklist:

- [ ] Non-placeholder `POSTGRES_PASSWORD`
- [ ] `API_AUTH_TOKEN` ≥ 24 characters, high entropy
- [ ] `APP_ENV=production`
- [ ] Explicit `CORS_ORIGINS` (no `*`)
- [ ] `LLM_API_KEY` if `LLM_PROVIDER` ≠ `mock`
- [ ] Host firewall / TLS terminator in front of published ports (out of Compose scope)

## 3. Database

Named volume `nova_pg` persists Postgres data.

On API start, `scripts/entrypoint.sh`:

1. Waits for `SELECT 1` within `DB_WAIT_SECONDS`
2. Runs `alembic upgrade head`
3. Starts uvicorn

**Do not** use `Base.metadata.create_all` in production. Schema changes are forward Alembic migrations only. Editing an already-applied revision on a persistent volume is unsupported.

Verify revision after start:

```bash
docker compose exec api alembic current
# expect: 0004_phase7_pipeline (head)
```

## 4. Startup

```bash
docker compose up -d
docker compose ps
```

Expected: `db` healthy → `api` healthy → `web` healthy.

## 5. Health checks

```bash
curl -sf "http://localhost:${API_PORT:-8000}/health"
curl -sf "http://localhost:${API_PORT:-8000}/ready"
curl -sf "http://localhost:${API_PORT:-8000}/metrics" | head
curl -sf "http://localhost:${WEB_PORT:-8080}/"
# Runtime config present; do not print token values in logs/tickets
curl -sf "http://localhost:${WEB_PORT:-8080}/runtime-config.js" | grep -q '__NOVA_RUNTIME__'
```

Automated smoke + recovery: `./scripts/verify-production-readiness.sh`.

## 6. Rollback

| Layer | Action |
|-------|--------|
| Application | Redeploy previous image tags (`docker compose` pin or registry tag); keep forward-compatible migrations |
| Schema | Prefer new forward migration. Downgrade only on disposable DBs; production downgrades are high-risk and must be rehearsed |
| Config | Revert `.env` / secret store; restart `api` / `web` |
| Data | Restore Postgres volume from backup (operator-owned; not automated in Part 1) |

## 7. Logs

JSON lines on container stdout (`docker compose logs -f api`). Fields: [../observability/logging.md](../observability/logging.md).

Never paste `Authorization`, `API_AUTH_TOKEN`, `DATABASE_URL`, or document bodies into tickets.

## 8. Common failures

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| API exits at start | Placeholder / weak production config | Fix `.env`; see configuration gates |
| `/ready` 503 | DB down or migrations incomplete | Check `db` health; `compose logs api`; wait for entrypoint |
| Migration error on start | Bad revision / dirty volume | See [../operations/recovery.md](../operations/recovery.md) |
| Web 502 on `/v1` | API not ready | Wait for API health; check network alias `api` |
| UI unauthenticated | Missing runtime config / token | Confirm `API_AUTH_TOKEN` on `web` and `/runtime-config.js` |
| 413 on upload | Body over `MAX_REQUEST_BODY_BYTES` / nginx `client_max_body_size` | Raise limits consistently or shrink file |

## Related

- [architecture.md](./architecture.md) · [local.md](./local.md) · [ci-cd.md](./ci-cd.md)
- [../operations/recovery.md](../operations/recovery.md)
- [../audits/phase-11-production-readiness.md](../audits/phase-11-production-readiness.md)
