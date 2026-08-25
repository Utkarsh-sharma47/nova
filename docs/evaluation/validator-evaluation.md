# Validator evaluation (Phase 5)

| Field | Value |
|-------|-------|
| Status | Implemented |
| Harness | `src/nova/evaluation/validator/` |
| Fixtures | `fixtures/evaluation/validator/` |
| Runner | `python scripts/run_validator_eval.py` |
| Reports | `docs/evaluation/reports/` and `docs/evaluation/results/` |

## Purpose

Measure Validator quality and prove safety invariants with synthetic labeled cases. Primary gate: **unsafe MATCH count must be 0**.

## Datasets

| Dataset | Path | Revision |
|---------|------|----------|
| Full eval | `fixtures/evaluation/validator/cases/` | `2026-08-25.1` |
| Fixed regression | `fixtures/evaluation/validator/regression/` | `2026-08-25.1` |

Categories: valid/invalid extraction, missing required, format/numeric/date/cross-field mismatch, conflicting/ambiguous/uncertain values, LLM disagreement/hallucination/override/timeout/malformed, database failure.

## Metrics

validation_accuracy, false_match_rate, false_mismatch_rate, uncertainty_rate, deterministic_rule_coverage, llm_assisted_validation_rate, mean_latency_ms, failure_rate, **unsafe_match_count/rate**.

## Measured results (MockLLM, no network)

Re-run `python scripts/run_validator_eval.py` after any rule/prompt/model change. Latest JSON reports are authoritative.

## Related

- [regression-policy.md](./regression-policy.md)
- [../agents/validator.md](../agents/validator.md)
- [../testing/validator-evaluation.md](../testing/validator-evaluation.md)
