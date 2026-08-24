# Architecture

High-level architecture for Nova.

## Purpose

Nova validates trade shipping documents with a multi-agent AI pipeline. Documents (for example Bill of Lading, invoice) are ingested, key fields are extracted, customer rules are applied, and the system produces a decision: auto-approve, human review, or request corrections.

## Current status

Phase 1 architecture principles and extension points are documented. No runtime stack, service topology, or persistence technology has been chosen yet. Stack choices will be ADRs in [`docs/decisions/`](docs/decisions/).

## Conceptual pipeline

```text
Document → ingestion → Extractor → confidence/evidence/presence
        → Validator → MATCH|MISMATCH|UNCERTAIN
        → Router → AUTO_APPROVE|HUMAN_REVIEW|AMENDMENT_REQUEST
        → persistence → query → UI
```

Detail: [`docs/product/solution-definition.md`](docs/product/solution-definition.md) and [`docs/architecture/high-level-overview.md`](docs/architecture/high-level-overview.md).

Agent **contracts and trust model** are defined (no runtime agents yet):

- [`docs/agents/contracts.md`](docs/agents/contracts.md)
- [`docs/agents/trust-model.md`](docs/agents/trust-model.md)
- [ADR-0002](docs/decisions/0002-ai-agent-contracts-and-trust-model.md)

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

- Language/runtime, API framework, database, LLM provider
- Orchestration model for agents
- Rules representation and customer configuration
- Schema IDL encoding for agent contracts
- API surface for intake, review, and NL query
- Evaluation harness tooling

Record each decision with the [ADR template](docs/decisions/ADR_TEMPLATE.md).

## Related documents

- [docs/architecture/](docs/architecture/)
- [docs/agents/](docs/agents/)
- [docs/agents/contracts.md](docs/agents/contracts.md)
- [docs/evaluation/agent-evaluation.md](docs/evaluation/agent-evaluation.md)
- [docs/decisions/](docs/decisions/)
- [ADR-0001](docs/decisions/0001-documentation-first-phase1.md)
- [ADR-0002](docs/decisions/0002-ai-agent-contracts-and-trust-model.md)
- [AGENTS.md](AGENTS.md)
