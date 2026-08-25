# Validator testing & evaluation

| Suite | Path |
|-------|------|
| Safety invariants | `tests/agents/validator/test_safety_invariants.py` |
| Deterministic unit | `tests/agents/validator/test_deterministic.py` |
| Failure injection | `tests/failure/validator/` |
| Eval harness tests | `tests/evaluation/validator/` |

## Commands

```bash
pytest -q tests/agents/validator tests/evaluation/validator tests/failure/validator
python scripts/run_validator_eval.py
```

## Safety invariants

1. Deterministic mismatch cannot become MATCH via LLM
2. Missing evidence cannot be treated as verified MATCH
3. LLM failure cannot become successful MATCH validation
4. Malformed LLM output cannot become valid MATCH
5. Historical validation results remain auditable (append-only)
