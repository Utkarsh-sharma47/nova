# Agents

Documentation for agents in the Nova pipeline.

## Purpose

Nova uses multiple agents to extract document fields, apply customer rules, and support decisioning. Each agent should have a dedicated document describing its contract and behavior.

## Conceptual roles (not yet implemented)

| Role | Responsibility |
|------|----------------|
| Extraction | Read documents and produce structured fields |
| Validation / rules | Compare fields to customer rules; emit findings |
| Decision support | Map findings to approve / review / corrections |

Exact agent names, counts, and orchestration are undecided. Record choices as ADRs and document each agent with the template below.

## Creating an agent doc

1. Copy [AGENT_TEMPLATE.md](AGENT_TEMPLATE.md).
2. Name the file clearly (for example `extraction-agent.md`).
3. Link it from this README when added.
4. Keep contracts synchronized with [`../api/`](../api/) and [`../architecture/`](../architecture/).

## Related

- [AGENT_TEMPLATE.md](AGENT_TEMPLATE.md)
- [AGENTS.md](../../AGENTS.md) (operating rules for AI coding agents)
- [Architecture](../architecture/)
- [Evaluation](../evaluation/)
