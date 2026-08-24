# Extractor evaluation

Deterministic evaluation harness for the Extractor Agent.

**Status:** Implemented  
**Dataset:** `fixtures/evaluation/extractor` (`extractor-golden` @ `extractor-regression-v1`)  
**Commands:** `python scripts/run-extractor-eval.py`, `python scripts/dogfood-extractor.py`

## Scope

Measures Extractor behavior on **synthetic** golden fixtures with scripted `MockLLM`
responses. This is **not** a claim of real LLM provider quality.

## Golden categories (12)

| Category | Intent |
|----------|--------|
| normal_document | Clean complete fields |
| missing_fields | Absent field → `MISSING`, no invention |
| ambiguous_values | Multiple candidates → `AMBIGUOUS` |
| conflicting_values | Header/body conflict → `AMBIGUOUS` |
| malformed_documents | Bad LLM JSON → `FAILED` after retries |
| misleading_document_text | Watermark/sample numbers ignored |
| prompt_injection_attempt | Injection text does not override extraction |
| fabricated_value_temptation | Ungrounded `KNOWN` downgraded |
| low_confidence_extraction | Low confidence retained / bounded |
| empty_document | No text → `FAILED` |
| partial_information | Blank values → `MISSING` |
| multiple_occurrences | Identical repeats remain `KNOWN` |

## Metrics (evaluation/test)

Computed against gold labels:

- field extraction accuracy
- exact match rate
- presence classification accuracy
- evidence availability rate
- schema validity rate
- fabrication rate
- unsupported-field rate
- failure rate
- latency (mean / p50 / p95)

These are **test/evaluation metrics**. They are distinct from per-field
**production confidence** on `ExtractedField`.

**Threshold policy:** no invented statistical SLOs. The regression gate is gold
agreement on the fixed dataset (visible FAIL + non-zero exit).

## Regression rule

```text
prompt / model / agent behavior change
  → run scripts/run-extractor-eval.py
  → regressions must be visible (FAIL), never silently accepted
  → do not delete/weaken gold cases to go green
```

See [regression-policy.md](./regression-policy.md).

## Dogfooding

```bash
python scripts/dogfood-extractor.py
python scripts/dogfood-extractor.py --case 08_fabricated_value_temptation
```

Prints per-field gold vs pred diffs for easy inspection.

## Hygiene

Synthetic fixtures only. Never commit real customer documents or secrets.

## Related

- [metrics.md](./metrics.md)
- [datasets.md](./datasets.md)
- [agent-evaluation.md](./agent-evaluation.md)
- [../agents/extractor.md](../agents/extractor.md)
- [../testing/extractor-evaluation.md](../testing/extractor-evaluation.md)
