# Deployment

| Doc | Purpose |
|-----|---------|
| [philosophy.md](./philosophy.md) | Simplicity |
| [architecture.md](./architecture.md) | Compose topology |
| [ci-cd.md](./ci-cd.md) | CI jobs |
| [local.md](./local.md) | Local Compose / Alembic |

ADR: [0008](../decisions/0008-deployment.md).

## Phase 3

`Dockerfile` runs `alembic upgrade head` then `uvicorn` (app factory).  
`docker-compose.yml` runs `api` + `postgres:16` with healthchecks and upload volume.
