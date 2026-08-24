# Evaluation architecture

Extends [philosophy.md](./philosophy.md). See also [evaluation-framework.md](./evaluation-framework.md), [metrics.md](./metrics.md), [agent-evaluation.md](./agent-evaluation.md).

## Harness

```text
fixtures/ → runner → agents (real or recorded) → metrics report → artifacts/
```

### Extractor (implemented)

Deterministic MockLLM harness:

```text
fixtures/evaluation/extractor/
  → nova.evaluation.extractor.runner
  → ExtractorService + MockLLM
  → metrics + failed-case report
```

Dogfood: `python scripts/run-extractor-eval.py` / `python scripts/dogfood-extractor.py`. Details: [extractor-evaluation.md](./extractor-evaluation.md).

Validator/Router harnesses remain Phase 5+ unless separately delivered.

## Mandatory metrics

| Metric | Gate |
|--------|------|
| False AUTO_APPROVE rate | 0 on labeled safety fixtures |
| Extraction field F1 (clean) | Track regression |
| UNCERTAIN/HUMAN_REVIEW on messy | Prefer over false approve |
| NL groundedness / refusal | Track |

Record model, prompt, contract, policy versions, git SHA.
