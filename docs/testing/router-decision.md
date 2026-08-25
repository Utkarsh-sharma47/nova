# Router / decision testing

| Suite | Path | Intent |
|-------|------|--------|
| Unit / safety | `tests/router/`, `tests/agents/router/` | Deterministic constraints, failsafe, LLM override |
| Contract | `tests/contracts/test_decision_safety.py` | `DecisionResult` cannot encode unsafe AUTO_APPROVE |
| Decision evaluation | `tests/evaluation/test_decision_evaluation.py` | Labeled regression + critical safety metrics |

## Regression gate

Changes to routing rules, prompts, models, or policy thresholds must run:

```bash
pytest -q tests/evaluation/test_decision_evaluation.py
```

Primary gate: **false AUTO_APPROVE rate = 0** on
`fixtures/evaluation/decision/` revision `2026-08-25.r1`
(evaluation-policy calibration target — see
[`docs/evaluation/decision-evaluation.md`](../evaluation/decision-evaluation.md)).

## Related

- [contract-requirements.md](./contract-requirements.md)
- [failure-testing.md](./failure-testing.md)
- Root [TESTING.md](../../TESTING.md)
