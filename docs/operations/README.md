# Operations

Operational practices and runbooks for Nova.

## Documents

| Document | Status |
|----------|--------|
| [git-workflow.md](./git-workflow.md) | Done — branch model, conventional commits, PR rules |
| [demo-runbook.md](./demo-runbook.md) | Done — Phase 12 submission Part 1 demo (synthetic fixtures) |
| [ui-demo.md](./ui-demo.md) | Done — Phase 9 synthetic UI demo flow |
| [recovery.md](./recovery.md) | Done — Phase 11 API/DB/web restart, migration failure, DB outage, verify script |

## Planned

| Topic | Status |
|-------|--------|
| On-call / ownership | Planned |
| Incident response | Planned |
| Backup and restore automation | Planned (volume restore is operator-owned today) |

## Guidance

- Link metrics and alerts from [`../observability/`](../observability/).
- Keep runbooks actionable and short.
- Never paste production secrets or raw customer documents into docs.
- Remote production deploy remains **NOT EXECUTED** until recorded in the Phase 11 audit — see [`../deployment/production.md`](../deployment/production.md).

## Related

- [Observability](../observability/)
- [Deployment](../deployment/)
- [Security](../security/)
- [CONTRIBUTING.md](../../CONTRIBUTING.md)
