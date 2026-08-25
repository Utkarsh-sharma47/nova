# ADR-0008: Deployment architecture (containers)

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-08-25 |
| Deciders | Principal Software Architect (Phase 2) |
| Supersedes | — |
| Superseded by | — |

## Context

### Problem

Part 1 needs a reproducible, low-ops deploy for demos.

### Requirements

- Reproducible runtime, env-based config, health checks, logs, rollback
- Part 2 extendable without full redesign

## Decision

Use **Docker** + **Docker Compose**:

| Service | Role |
|---------|------|
| `api` | FastAPI ASGI app |
| `db` | PostgreSQL |
| `web` | React static UI (Phase 6) |

Part 1 default: **api + db**. No Kubernetes or mandatory message queue for Part 1.

## Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| Bare venv only | Simple for dev | Weak demo reproducibility |
| Kubernetes | Scale | Beyond Part 1 |
| Serverless only | Ops light | Awkward multi-stage pipeline |
| PaaS without containers | Fast host | Still benefit from container contract |

## Consequences

### Advantages

Same artifact locally and in demo host.

### Disadvantages

Contributors need Docker; OCR may grow image size.

### Operational cost

Low: two containers for core demo.

### Complexity

Low.

### Developer velocity

High once Compose is documented.

### Testing implications

Contract tests without Compose; integration may use Compose later.

### Deployment implications

Rollback = prior image tag + migration compatibility.

### Part 2 compatibility

Add worker containers without changing api/db contracts.

### Migration risk

Low.

## Compliance

- `Dockerfile` and `docker-compose.yml` describe shape.
- Secrets only via env/secret store.

## References

- `REQ-DEPLOY-003`, `REQ-DEPLOY-004`
- [`docs/deployment/architecture.md`](../deployment/architecture.md)
