# Evaluation

Quality and accuracy evaluation for Nova’s extraction, validation, and decisioning.

## Documents

| Document | Status |
|----------|--------|
| [philosophy.md](./philosophy.md) | Done |
| [architecture.md](./architecture.md) | Done |
| [evaluation-framework.md](./evaluation-framework.md) | Done |
| [agent-evaluation.md](./agent-evaluation.md) | Done |
| [validator-evaluation.md](./validator-evaluation.md) | Done — Validator harness + reports |
| [decision-evaluation.md](./decision-evaluation.md) | Done — Router decision harness + dataset |
| [datasets.md](./datasets.md) | Done — validator + decision fixtures |
| [metrics.md](./metrics.md) | Done — calibration targets recorded |
| [regression-policy.md](./regression-policy.md) | Done — fixed-dataset eval on prompt/model changes |

## Current status

| Area | Status |
|------|--------|
| Router decision evaluation | Implemented (`nova.evaluation.decision`, `fixtures/evaluation/decision/`) |
| Validator evaluation | Implemented (`nova.evaluation.validator`, fixtures + reports) |
| Phase 7 pipeline regression | E2E suite `tests/pipeline/` (MockLLM); does not replace agent eval gates |
| Phase 10 full evaluation command | `scripts/run_full_evaluation.py` (validator + decision + extractor fabrication) |
| Live LLM quality jobs | Not in this suite |

Primary Router safety gate: **false AUTO_APPROVE rate = 0.0** on regression
revision `2026-08-25.r1` (evaluation-policy calibration target — not a production SLO claim).

## Principles

- Separate **evaluation** (quality) from **tests** (correctness of code contracts).
- Use anonymized or synthetic documents only.
- Report methodology and limitations with every result.
- Never fabricate evaluation outcomes.
- Prompt/model/policy changes are behavioral changes — see [trust-model](../agents/trust-model.md)
  and [regression-policy](./regression-policy.md).

## Related

- [Testing](../testing/)
- [Agents](../agents/)
- [Audits](../audits/)
- [ADR-0010](../decisions/0010-ai-agent-contracts-and-trust-model.md)
- Requirements `REQ-EXT-005`, `REQ-ROUTER-*`, `REQ-SUBMISSION-002`
