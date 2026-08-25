# Agents

Documentation for agents in the Nova pipeline (Extractor, Validator, Router).

## Purpose

Each runtime agent has a dedicated document describing its typed contract and behavior. AI coding agents that *implement* Nova must follow root [`AGENTS.md`](../../AGENTS.md).

**Canonical contracts:** [contracts.md](./contracts.md)  
**Trust model:** [trust-model.md](./trust-model.md)  
**ADR:** [ADR-0010](../decisions/0010-ai-agent-contracts-and-trust-model.md)

Contracts and agents are **implemented** for Part 1. Default LLM path is `MockLLM` (deterministic). Optional live OpenAI-compatible provider is available behind `LLMPort` when credentials are configured.

## Agents

| Agent | Doc | Role | Status |
|-------|-----|------|--------|
| Extractor | [extractor.md](./extractor.md) | Fields + confidence + evidence + presence | Implemented |
| Validator | [validator.md](./validator.md) | Customer rules → MATCH / MISMATCH / UNCERTAIN | Implemented |
| Router | [router.md](./router.md) | AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST | Implemented |

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
- [ADR-0010](../decisions/0010-ai-agent-contracts-and-trust-model.md)
- [GoComet submission](../submission/)
