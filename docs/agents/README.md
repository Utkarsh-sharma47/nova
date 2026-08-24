# Agents

Documentation for agents in the Nova pipeline (Extractor, Validator path, Router, and later communication agents).

## Purpose

Each runtime agent should have a dedicated document describing its typed contract and behavior. AI coding agents that *implement* Nova must follow root [`AGENTS.md`](../../AGENTS.md).

## Conceptual roles (not yet implemented)

| Role | Responsibility |
|------|----------------|
| Extraction | Read documents; produce fields with confidence and evidence |
| Validation | Compare fields to customer rules; MATCH / MISMATCH / UNCERTAIN |
| Router | AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST |

## Creating an agent doc

1. Copy [AGENT_TEMPLATE.md](AGENT_TEMPLATE.md).
2. Name the file clearly (for example `extractor-agent.md`).
3. Link it from this README when added.
4. Keep contracts synchronized with [`../api/`](../api/) and [`../architecture/`](../architecture/).
5. Trace to `REQ-AI-*`, `REQ-EXT-*`, `REQ-VAL-*`, `REQ-ROUTER-*`.

## Related

- [AGENT_TEMPLATE.md](AGENT_TEMPLATE.md)
- [AGENTS.md](../../AGENTS.md)
- [Solution definition](../product/solution-definition.md)
- [Architecture principles](../architecture/principles.md)
- [Part 2 extension points](../architecture/part2-extension-points.md)
