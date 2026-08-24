# Testing

| Doc | Purpose |
|-----|---------|
| [philosophy.md](./philosophy.md) | Goals |
| [contract-requirements.md](./contract-requirements.md) | Required suites |
| [test-strategy.md](./test-strategy.md) | Pyramid / layers |
| [contract-testing.md](./contract-testing.md) | Contract surfaces |
| [failure-testing.md](./failure-testing.md) | Fail-safe catalog |
| [performance-testing.md](./performance-testing.md) | Latency/cost intents |
| [document-processing.md](./document-processing.md) | Document processor suites |
| [extractor-evaluation.md](./extractor-evaluation.md) | Extractor golden/regression + dogfood |

Root: [TESTING.md](../../TESTING.md).

## Automated checks (current)

```bash
ruff check src tests
mypy
pytest -q
python scripts/run-extractor-eval.py
```

## Principles

- Tests must be runnable and honest; never fabricate results.
- Prefer deterministic fixtures; isolate provider-dependent checks under evaluation.
- Evaluation regressions must be visible (non-zero exit).
