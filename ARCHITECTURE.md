# Architecture

High-level architecture for Nova.

## Purpose

Nova validates trade shipping documents with a multi-agent AI pipeline. Documents (for example Bill of Lading, invoice) are ingested, key fields are extracted, customer rules are applied, and the system produces a decision: auto-approve, human review, or request corrections.

## Current status

Architecture is at the documentation foundation stage. No runtime stack, service topology, or persistence technology has been decided. Decisions will be recorded as ADRs in [`docs/decisions/`](docs/decisions/).

## Conceptual pipeline

```text
Document intake
      │
      ▼
Extraction agents          → structured fields
      │
      ▼
Validation / rules agents  → rule results and findings
      │
      ▼
Decisioning                → approve | review | request corrections
      │
      ▼
Human review / feedback    → (optional) corrections loop
```

This diagram is conceptual. Agent boundaries, orchestration, and storage are not yet fixed.

## Design principles

- **Contracts first.** Agent inputs/outputs and external interfaces should be explicit and versioned.
- **Human-in-the-loop.** Ambiguous or high-risk cases escalate to review rather than silent auto-approval.
- **Auditability.** Decisions should be explainable from logged inputs, rule results, and agent outputs.
- **Scoped evolution.** Subsystems change via ADRs; avoid silent architectural drift.
- **Security by default.** Treat document contents as sensitive; see [SECURITY.md](SECURITY.md).

## Documentation structure

Detailed architecture notes live under [`docs/architecture/`](docs/architecture/). Agent design lives under [`docs/agents/`](docs/agents/). Feature-level design uses the feature template in [`docs/features/`](docs/features/).

## Open decisions

Examples of decisions still to be made (non-exhaustive):

- Orchestration model for agents
- Document storage and retention
- Rules representation and customer configuration
- API surface for intake and review
- Evaluation harness and gold datasets

Record each decision with the [ADR template](docs/decisions/ADR_TEMPLATE.md).

## Related documents

- [docs/architecture/](docs/architecture/)
- [docs/agents/](docs/agents/)
- [docs/decisions/](docs/decisions/)
- [AGENTS.md](AGENTS.md)
