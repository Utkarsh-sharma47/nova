# Validator testing & evaluation

| Field | Value |
|-------|-------|
| Status | Implemented (Phase 5) |
| Unit / safety | `tests/agents/validator/` |
| Failure | `tests/failure/validator/` |
| Evaluation | `tests/evaluation/validator/` + `scripts/run_validator_eval.py` |

## Safety invariants (automated)

| # | Invariant | Test |
|---|-----------|------|
| 1 | Deterministic mismatch cannot become MATCH via LLM | `test_deterministic_mismatch_cannot_become_match_via_llm` |
| 2 | Missing evidence cannot be treated as verified MATCH | `test_missing_evidence_cannot_be_treated_as_verified_match` |
| 3 | LLM failure cannot become successful MATCH validation | `test_llm_failure_cannot_become_successful_validation` |
| 4 | Malformed LLM output cannot become valid MATCH | `test_malformed_llm_output_cannot_become_valid_match` |
| 5 | Historical validation results remain auditable (append-only) | `test_historical_validation_results_remain_auditable` |

Additional failure coverage: provider failure, illegal LLM outcomes, database persistence failure, FAILED extraction.

## Commands

```bash
pytest -q tests/agents/validator tests/evaluation/validator tests/failure/validator
python scripts/run_validator_eval.py
```

## Related

- [failure-testing.md](./failure-testing.md)
- [../evaluation/validator-evaluation.md](../evaluation/validator-evaluation.md)
- [../agents/validator.md](../agents/validator.md)
