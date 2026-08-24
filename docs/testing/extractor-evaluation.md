# Extractor evaluation testing

How to run and interpret Extractor evaluation in Nova.

## Commands

```bash
pip install -e ".[dev]"
python scripts/run-extractor-eval.py
python scripts/dogfood-extractor.py
pytest -q tests/evaluation tests/extraction
```

Exit code `0` = gold agreement on the fixed regression revision.  
Exit code `1` = visible regression(s) — investigate; do not weaken fixtures.

## What is covered

| Layer | Location |
|-------|----------|
| Extractor unit (MockLLM) | `tests/extraction/` |
| Eval metrics / scorer | `tests/evaluation/` |
| Golden + regression suite | `fixtures/evaluation/extractor/` + `scripts/run-extractor-eval.py` |
| Dogfood inspection | `scripts/dogfood-extractor.py` |

## Metrics vs confidence

Suite metrics (accuracy, fabrication rate, …) are **evaluation/test measurements**.
Per-field `confidence` on `ExtractedField` is **production confidence** for
downstream agents. Do not conflate them. Do not invent SLOs without baselines.

## Related

- [extractor-evaluation.md](../evaluation/extractor-evaluation.md)
- [regression-policy.md](../evaluation/regression-policy.md)
- [../agents/extractor.md](../agents/extractor.md)
