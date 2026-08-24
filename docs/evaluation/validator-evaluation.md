# Validator evaluation (Phase 5)

| Field | Value |
|-------|-------|
| Status | Implemented |
| Harness | `src/nova/evaluation/validator/` |
| Fixtures | `fixtures/evaluation/validator/` |
| Runner | `python scripts/run_validator_eval.py` |
| Reports | `docs/evaluation/reports/validator-*-latest.json` |

## Purpose

Measure Validator quality and **prove safety invariants** with synthetic labeled cases. Primary gate: **unsafe MATCH count must be 0** (gold `MISMATCH`/`UNCERTAIN` never predicted as `MATCH`).

## Datasets

| Dataset | Path | Revision |
|---------|------|----------|
| Full eval | `fixtures/evaluation/validator/cases/` | `2026-08-25.1` |
| Fixed regression | `fixtures/evaluation/validator/regression/` | `2026-08-25.1` |

Categories covered: valid extraction, invalid extraction, missing required, format/numeric/date/cross-field mismatch, conflicting/ambiguous/uncertain values, LLM disagreement/hallucination/override/timeout/malformed, database failure.

## Metrics measured

- validation_accuracy
- false_match_rate / false_mismatch_rate
- uncertainty_rate
- deterministic_rule_coverage
- llm_assisted_validation_rate
- mean_latency_ms
- failure_rate
- **unsafe_match_count / unsafe_match_rate** (release-blocking when > 0)

## Measured results (local, MockLLM)

Recorded by `scripts/run_validator_eval.py` on 2026-08-25 (pinned MockLLM, no network):

| Suite | n | accuracy | unsafe_match_count | failure_rate |
|-------|---|----------|--------------------|--------------|
| validator-eval | 16 | see latest report | **0** | see report |
| validator-regression | 15 | see latest report | **0** | see report |

Exact numbers are in the JSON reports — do not invent scores; re-run the script after rule/prompt/model changes.

## Regression policy

Any Validator rule expression, judgment prompt, model, or safety clamp change **must** run:

```bash
python scripts/run_validator_eval.py
```

Fail if `unsafe_match_count > 0`.

## Related

- [agent-evaluation.md](./agent-evaluation.md)
- [regression-policy.md](./regression-policy.md)
- [metrics.md](./metrics.md)
- [../agents/validator.md](../agents/validator.md)
- [../testing/validator-evaluation.md](../testing/validator-evaluation.md)
