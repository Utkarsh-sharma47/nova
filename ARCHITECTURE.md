# Architecture

High-level architecture for Nova.

## Purpose

Nova validates trade shipping documents with a multi-agent AI pipeline. Documents (for example Bill of Lading, invoice) are ingested, key fields are extracted, customer rules are applied, and the system produces a decision: auto-approve, human review, or request corrections.

## Current status

Phase 1 principles and extension points are documented. Phase 2 is defining stack ADRs and typed contracts. **Part 1 HTTP API contracts are specified** under [`docs/api/`](docs/api/) (no runtime routes yet).

## Conceptual pipeline

```text
Document → ingestion → extraction → confidence/evidence
        → validation → routing → persistence → query → UI
```

Detail: [`docs/product/solution-definition.md`](docs/product/solution-definition.md) and [`docs/architecture/high-level-overview.md`](docs/architecture/high-level-overview.md).

## External API (Part 1 contracts)

Public HTTP surface (contracts only; FastAPI implementation later):

| Area | Method | Path |
|------|--------|------|
| Document ingestion | `POST` | `/v1/documents` |
| Document retrieval | `GET` | `/v1/documents/{document_id}` |
| Shipment retrieval | `GET` | `/v1/shipments/{shipment_id}` |
| Validation results | `GET` | `/v1/documents/{document_id}/validation` |
| Decision results | `GET` | `/v1/documents/{document_id}/decision` |
| Natural-language query | `POST` | `/v1/query` |
| Health | `GET` | `/health` |
| Readiness | `GET` | `/ready` |

Normative docs:

- [`docs/api/contracts.md`](docs/api/contracts.md)
- [`docs/api/error-model.md`](docs/api/error-model.md)
- [`docs/api/versioning.md`](docs/api/versioning.md)
- [`docs/api/idempotency.md`](docs/api/idempotency.md)
- [`docs/api/query-interface.md`](docs/api/query-interface.md)

API layering: routes → application services → domain/agent ports → infrastructure. NL query must use allow-listed plans only — **no arbitrary LLM-generated SQL execution**.

## Design principles

See the full list in [`docs/architecture/principles.md`](docs/architecture/principles.md). Highlights:

- Typed contracts; deterministic validation where appropriate; LLMs where reasoning is needed
- Confidence-aware extraction with evidence/grounding
- Human-in-the-loop; no silent auto-approve on failure
- Observability, idempotency, bounded retries, cost controls
- Part 2 extensibility without implementing Part 2 now

## Part 2 readiness

[`docs/architecture/part2-extension-points.md`](docs/architecture/part2-extension-points.md)

## Open decisions (Phase 2+)

- Stack ADRs (language, API framework, database, LLM provider) — in progress under [`docs/decisions/`](docs/decisions/)
- Orchestration model for agents
- Rules representation and customer configuration
- Evaluation harness tooling

Record each decision with the [ADR template](docs/decisions/ADR_TEMPLATE.md).

## Related documents

- [docs/architecture/](docs/architecture/)
- [docs/api/](docs/api/)
- [docs/agents/](docs/agents/)
- [docs/decisions/](docs/decisions/)
- [ADR-0001](docs/decisions/0001-documentation-first-phase1.md)
- [AGENTS.md](AGENTS.md)
