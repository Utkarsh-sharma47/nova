# Evaluation

Quality and accuracy evaluation for Nova’s extraction, validation, and decisioning.

## Documents

| Document | Status |
|----------|--------|
| [philosophy.md](./philosophy.md) | Done |
| [agent-evaluation.md](./agent-evaluation.md) | Spec + Extractor harness linked |
| [evaluation-framework.md](./evaluation-framework.md) | Done |
| [datasets.md](./datasets.md) | Done + Extractor fixtures landed |
| [metrics.md](./metrics.md) | Done — definitions; thresholds as calibration targets |
| [regression-policy.md](./regression-policy.md) | Done — mandatory fixed-dataset eval |
| [extractor-evaluation.md](./extractor-evaluation.md) | **Implemented** — deterministic Extractor suite |
| [architecture.md](./architecture.md) | Done |

## Current status

| Area | Status |
|------|--------|
| Extractor golden/regression harness | **Implemented** (`fixtures/evaluation/extractor`, `scripts/run-extractor-eval.py`) |
| Validator / Router eval harness | Not implemented |
| Real-provider measured scores | **Not claimed** (MockLLM / scripted fixtures only) |

```bash
python scripts/run-extractor-eval.py
python scripts/dogfood-extractor.py
```

## Principles

- Separate **evaluation** (quality vs gold) from **unit/contract tests** (code correctness).
- Separate **evaluation metrics** from **production confidence**.
- Synthetic or anonymized documents only.
- Never fabricate evaluation outcomes.
- Prompt/model/agent changes require regression eval — failures must be visible.

## Related

- [Testing](../testing/)
- [Agents](../agents/)
- [ADR-0010](../decisions/0010-ai-agent-contracts-and-trust-model.md)
- Requirements `REQ-EXT-005`, `REQ-SUBMISSION-002`, `REQ-AI-004`
