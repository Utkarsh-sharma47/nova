# Testing contract requirements

Tests that **later implementations must provide**. Phase 2 implements **schema/contract tests only**.

## Required suites (by phase)

| Suite | Intent | Owner phase | CI |
|-------|--------|-------------|-----|
| **Unit** | Deterministic parsers, rule operators, policy matrix, confidence banding | 3–4 | always |
| **Integration** | Pipeline wiring + Postgres + HTTP | 5–6 | always |
| **Contract** | Pydantic agent/API schemas; OpenAPI stability | **2+** | always |
| **Agent** | MockLLM behavioral tests per agent | 3–4 | always |
| **Evaluation** | Live/fixture LLM quality; false AUTO_APPROVE | 5–7 | gated/manual |
| **Regression** | Golden fixtures for validation/routing | 4–5 | always |
| **Failure** | Timeouts, provider errors, malformed docs, retry exhaustion | 3–4 | always |
| **Performance** | Smoke latency budgets for demo sizes | 7 | optional/scheduled |

## Phase 2 delivered

- `tests/contracts/` — valid/invalid instantiations of domain contracts
- No fake “always pass” application tests beyond real schema assertions

## Invariants every future PR must protect

1. Invalid agent payloads rejected by schema
2. `DecisionResult.decision` only allows documented enums
3. `ValidationCheck.outcome` only MATCH/MISMATCH/UNCERTAIN
4. ErrorResponse always exposes `retryable` + `error_code`
5. No test disables safety assertions to go green

## Related

- [philosophy.md](./philosophy.md)
- `TESTING.md`
- ADR-0002
