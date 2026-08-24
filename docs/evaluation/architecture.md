# Evaluation architecture

Extends [philosophy.md](./philosophy.md). See also [evaluation-framework.md](./evaluation-framework.md), [metrics.md](./metrics.md), [agent-evaluation.md](./agent-evaluation.md).

## Harness (Phase 5+)

```text
fixtures/ → runner → agents (real or recorded) → metrics report → artifacts/
```

## Mandatory metrics

| Metric | Gate |
|--------|------|
| False AUTO_APPROVE rate | 0 on labeled safety fixtures |
| Extraction field F1 (clean) | Track regression |
| UNCERTAIN/HUMAN_REVIEW on messy | Prefer over false approve |
| NL groundedness / refusal | Track |

Record model, prompt, contract, policy versions, git SHA.
