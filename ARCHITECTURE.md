# Architecture

High-level architecture for Nova.

## Purpose

Nova validates trade shipping documents with a multi-agent AI pipeline. Documents (for example Bill of Lading, invoice) are ingested, key fields are extracted, customer rules are applied, and the system produces a decision: auto-approve, human review, or request corrections.

## Current status

Phase 1 principles and extension points are documented. Phase 2 is defining stack ADRs and typed contracts.

**Specified so far (contracts/design only — no runtime services yet):**

- Agent contracts / trust model ([`docs/agents/`](docs/agents/))
- Part 1 HTTP API contracts ([`docs/api/`](docs/api/))
- Domain model + PostgreSQL schema design ([`docs/database/`](docs/database/), persistence ADR)

## Conceptual pipeline

```text
Document → ingestion → Extractor → confidence/evidence/presence
        → Validator → MATCH|MISMATCH|UNCERTAIN
        → Router → AUTO_APPROVE|HUMAN_REVIEW|AMENDMENT_REQUEST
        → persistence → query → UI
```

Detail: [`docs/product/solution-definition.md`](docs/product/solution-definition.md) and [`docs/architecture/high-level-overview.md`](docs/architecture/high-level-overview.md).

Persistence stores shipment-centric, multi-document data. See [`docs/database/`](docs/database/).

## Agent contracts (Phase 2)

- [`docs/agents/contracts.md`](docs/agents/contracts.md)
- [`docs/agents/trust-model.md`](docs/agents/trust-model.md)
- ADR for AI contracts (see [`docs/decisions/`](docs/decisions/); numbering reconciled during integration)

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

Normative docs: [`docs/api/contracts.md`](docs/api/contracts.md), [error-model](docs/api/error-model.md), [versioning](docs/api/versioning.md), [idempotency](docs/api/idempotency.md), [query-interface](docs/api/query-interface.md).

API layering: routes → application services → domain/agent ports → infrastructure. NL query must use allow-listed plans only — **no arbitrary LLM-generated SQL execution**.

## Persistence (Phase 2 design)

| Concern | Decision |
|---------|----------|
| Primary store | PostgreSQL (see persistence ADR under `docs/decisions/`) |
| Document bytes | Object storage via URI + content hash on `document_versions` |
| Domain model | [`docs/database/domain-model.md`](docs/database/domain-model.md) |
| Schema | [`docs/database/schema-design.md`](docs/database/schema-design.md) |

## Design principles

See the full list in [`docs/architecture/principles.md`](docs/architecture/principles.md). Highlights:

- Typed contracts; deterministic validation where appropriate; LLMs where reasoning is needed
- Confidence-aware extraction with evidence/grounding
- Human-in-the-loop; no silent auto-approve on failure
- Observability, idempotency, bounded retries, cost controls
- Auditability from stored fields, rule results, and audit events
- Part 2 extensibility (shipment 1→N documents) without implementing Part 2 now

## Part 2 readiness

[`docs/architecture/part2-extension-points.md`](docs/architecture/part2-extension-points.md)

## Open decisions (Phase 2+)

- Remaining stack ADRs (language/runtime, API framework, LLM provider, object storage) — under [`docs/decisions/`](docs/decisions/)
- Orchestration model for agents
- Rules representation / `definition_json` schemas
- Schema IDL encoding for agent contracts (Pydantic as working encoding)
- Evaluation harness tooling

Record each decision with the [ADR template](docs/decisions/ADR_TEMPLATE.md).

## Related documents

- [docs/architecture/](docs/architecture/)
- [docs/api/](docs/api/)
- [docs/database/](docs/database/)
- [docs/agents/](docs/agents/)
- [docs/agents/contracts.md](docs/agents/contracts.md)
- [docs/evaluation/agent-evaluation.md](docs/evaluation/agent-evaluation.md)
- [docs/decisions/](docs/decisions/)
- [ADR-0001](docs/decisions/0001-documentation-first-phase1.md)
- [AGENTS.md](AGENTS.md)
