# Operations

Operational practices and runbooks for Nova.

## Documents (Phase 1)

| Document | Status |
|----------|--------|
| [git-workflow.md](./git-workflow.md) | Done — branch model, conventional commits, PR rules |

## Planned (when the system is operable)

| Topic | Status |
|-------|--------|
| On-call / ownership | Planned |
| Incident response | Planned |
| Common failure runbooks | Planned |
| Backup and restore (if applicable) | Planned |
| Demo / submission runbook | Phase 8 |
| Pipeline operations notes | Phase 7 — see [`../architecture/end-to-end-pipeline.md`](../architecture/end-to-end-pipeline.md) |
| Local pipeline baseline | `scripts/benchmark_pipeline.py` (MockLLM; not a production SLO) |

## Guidance

- Link metrics and alerts from [`../observability/`](../observability/).
- Keep runbooks actionable and short.
- Never paste production secrets or raw customer documents into docs.

## Related

- [Observability](../observability/)
- [Deployment](../deployment/)
- [Security](../security/)
- [CONTRIBUTING.md](../../CONTRIBUTING.md)
