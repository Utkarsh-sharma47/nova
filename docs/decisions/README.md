# Architecture Decision Records

ADRs record significant decisions. Use sequential IDs and the template.

| ID | Title | Status |
|----|-------|--------|
| [0001](./0001-documentation-first-phase1.md) | Documentation-first Phase 1 foundation | Accepted |
| [0002](./0002-backend-stack.md) | Backend stack (Python, Pydantic, SQLAlchemy, Alembic, pytest, Ruff, MyPy) | Accepted |
| [0003](./0003-database.md) | Database (PostgreSQL 16) | Accepted |
| [0004](./0004-api-framework.md) | API framework (FastAPI) | Accepted |
| [0005](./0005-ai-provider-abstraction.md) | AI provider abstraction (`LLMPort`) | Accepted |
| [0006](./0006-document-processing.md) | Document processing / OCR port | Accepted |
| [0007](./0007-observability.md) | Observability (logs, metrics, health) | Accepted |
| [0008](./0008-deployment.md) | Deployment (Docker / Compose) | Accepted |
| [0009](./0009-frontend-stack.md) | Frontend (React, TypeScript, Vite) | Accepted |
| [0010](./0010-ai-agent-contracts-and-trust-model.md) | AI agent contracts and trust model | Accepted |

## When to write an ADR

- Technology stack selection
- Agent contract shape changes
- Persistence technology choice
- Routing policy framework choice
- Part 2 interface changes that affect Part 1

## Creating an ADR

1. Copy [ADR_TEMPLATE.md](ADR_TEMPLATE.md).
2. Use the next numeric ID and a short slug filename.
3. Set status to Proposed → Accepted / Rejected / Superseded.
4. Link it from this README.
5. Update related architecture/requirements docs in the same PR.
6. When superseding, update both old and new ADRs.

## Related

- [ADR_TEMPLATE.md](ADR_TEMPLATE.md)
- [Architecture](../architecture/)
- [Database](../database/)
- [Agents](../agents/)
- [AGENTS.md](../../AGENTS.md)
