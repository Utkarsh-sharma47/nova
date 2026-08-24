# Evaluation

Quality and accuracy evaluation for Nova’s extraction, validation, and decisioning.

## Documents

| Document | Status |
|----------|--------|
| [philosophy.md](./philosophy.md) | Done (Phase 1) |
| [agent-evaluation.md](./agent-evaluation.md) | Done (spec only — no harness) |

## Current status

No evaluation harness or gold dataset exists yet. Do not invent scores or claim unmeasured quality.

[agent-evaluation.md](./agent-evaluation.md) defines required test classes (contract, schema, golden, datasets, adversarial, failure, regression) and the false `AUTO_APPROVE` safety bar for Extractor / Validator / Router.

## Planned contents

| Topic | Status |
|-------|--------|
| Metrics (field-level, document-level, decision agreement) | Spec’d in agent-evaluation; harness later |
| Gold / labeled datasets (clean + messy samples) | Phase 5 |
| Regression evaluation process | Spec’d; automation Phase 5–7 |
| False AUTO_APPROVE safety bar | Spec’d as primary gate |

## Principles

- Separate **evaluation** (quality) from **tests** (correctness of code contracts).
- Use anonymized or synthetic documents only.
- Report methodology and limitations with every result.
- Never fabricate evaluation outcomes.
- Prompt/model changes are behavioral changes — see [trust-model](../agents/trust-model.md).

## Related

- [Testing](../testing/)
- [Agents](../agents/)
- [Audits](../audits/)
- [ADR-0002](../decisions/0002-ai-agent-contracts-and-trust-model.md)
- Requirements `REQ-EXT-005`, `REQ-SUBMISSION-002`
