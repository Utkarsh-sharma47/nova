# Agents

Documentation for agents in the Nova pipeline (Extractor, Validator, Router).

## Purpose

Each runtime agent has a dedicated document describing its typed contract and behavior. AI coding agents that *implement* Nova must follow root [`AGENTS.md`](../../AGENTS.md).

**Canonical contracts:** [contracts.md](./contracts.md)  
**Trust model:** [trust-model.md](./trust-model.md)  
**ADR:** [ADR-0002](../decisions/0002-ai-agent-contracts-and-trust-model.md)

Contracts are defined; **agents are not implemented** (no LLM provider calls in this phase).

## Agents

| Agent | Doc | Role |
|-------|-----|------|
| Extractor | [extractor.md](./extractor.md) | Fields + confidence + evidence + presence |
| Validator | [validator.md](./validator.md) | Customer rules → MATCH / MISMATCH / UNCERTAIN |
| Router | [router.md](./router.md) | AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST |

## Shared governance

| Document | Purpose |
|----------|---------|
| [contracts.md](./contracts.md) | Typed request/result schemas and invariants |
| [trust-model.md](./trust-model.md) | Probabilistic LLM controls + prompt governance |
| [AGENT_TEMPLATE.md](./AGENT_TEMPLATE.md) | Template for additional agents |

## Creating or changing an agent doc

1. Prefer updating [contracts.md](./contracts.md) before agent prose.
2. Keep extractor/validator/router docs aligned with contracts.
3. Breaking contract changes require a new or superseding ADR.
4. Prompt/model behavioral changes follow trust-model prompt governance and [agent-evaluation](../evaluation/agent-evaluation.md).
5. Trace to `REQ-AI-*`, `REQ-EXT-*`, `REQ-VAL-*`, `REQ-ROUTER-*`.

## Related

- [AGENTS.md](../../AGENTS.md)
- [Architecture](../architecture/)
- [Evaluation](../evaluation/)
- [ADR-0002](../decisions/0002-ai-agent-contracts-and-trust-model.md)
