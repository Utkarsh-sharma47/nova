# Deployment architecture

ADR: [0008](../decisions/0008-deployment.md). Philosophy: [philosophy.md](./philosophy.md).

## Part 1 topology

```text
┌────────────┐     ┌────────────┐     ┌────────────┐
│  web (UI)  │────▶│    api     │────▶│  postgres  │
│  (Phase 9) │     │  FastAPI   │     │            │
└────────────┘     └─────┬──────┘     └────────────┘
                         │
                   object storage / volume
                   (document bytes)
```

Compose services: `api`, `db`, `web` (nginx static UI + `/v1` proxy).

## Priorities

| Priority | How addressed |
|----------|---------------|
| Easy deployment | `docker compose up` |
| Low ops complexity | No K8s, no required queue |
| Reproducibility | Tagged images + lockfiles + model/prompt versions in data |
| Environment config | `.env` / host env |
| Health checks | `/health`, `/ready` |
| Logs | JSON stdout |
| Rollback | Prior image tag; forward-compatible migrations |

## Configuration (illustrative)

```bash
DATABASE_URL=postgresql+psycopg://nova:***@db:5432/nova
LLM_PROVIDER=mock|openai|anthropic|...
LLM_API_KEY=
LLM_MODEL=
LOG_LEVEL=INFO
API_AUTH_TOKEN=
```

## Part 2 extension

Add `worker` service consuming ingestion jobs; same image possible with different command. No redesign of api/db contracts.

## Phase 2 artifacts

- `Dockerfile` — Python API image skeleton
- `docker-compose.yml` — api + db shape

No production business logic in images yet.
