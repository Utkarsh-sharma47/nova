# Deployment

Part 1 deployment for Nova uses **Docker Compose** (`api` + `db` + `web`). Phase 11 hardens images, configuration, health/metrics, and recovery runbooks.

**Remote / cloud production deploy: NOT EXECUTED.** Procedures in [production.md](./production.md) are documented for operators; no remote host was provisioned or smoke-tested in this phase.

| Doc | Purpose |
|-----|---------|
| [philosophy.md](./philosophy.md) | Simplicity and low-ops bias |
| [architecture.md](./architecture.md) | Compose topology, non-root, runtime secrets |
| [configuration.md](./configuration.md) | Full environment variable reference |
| [local.md](./local.md) | Local Compose notes (runtime-config injection) |
| [frontend.md](./frontend.md) | Ops UI image, nginx-unprivileged, no baked auth |
| [production.md](./production.md) | Build → config → DB → startup → health → rollback → logs → failures |
| [ci-cd.md](./ci-cd.md) | GitHub Actions jobs (Python, frontend, Docker, audits) |

ADR: [0008](../decisions/0008-deployment.md).

Production readiness checklist: [../audits/phase-11-production-readiness.md](../audits/phase-11-production-readiness.md).

Verify locally (Compose smoke + recovery):

```bash
./scripts/verify-production-readiness.sh
```
