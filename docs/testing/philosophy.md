# Testing philosophy

## Goals

Prove deterministic behavior quickly in CI; evaluate probabilistic LLM behavior with explicit harnesses; never fake green.

## Layers (as code appears)

| Layer | What | When in CI |
|-------|------|------------|
| Unit | Parsers, rule evaluation, policy thresholds, schema validation | Always |
| Contract | Agent I/O schemas, API request/response shapes | Always |
| Integration | Pipeline stage wiring + persistence | Always (may use testcontainers/sqlite later) |
| Failure | Timeouts, provider errors, malformed docs | Always for critical paths |
| Evaluation | LLM quality on fixtures (clean/messy) | Scheduled or manual/gated — not flaky silent CI |
| UI smoke | Critical ops paths | Smoke job when UI exists |

## Rules

1. **No fake tests** — A test must be able to fail for a real regression.
2. **No application test suite until application code exists** — Phase 1 CI validates docs/secrets only.
3. **Golden fixtures** for MATCH/MISMATCH/UNCERTAIN and all router decisions.
4. **Deterministic seeds/config** for any sampling-based components where possible.
5. **Honest reporting** — Failed evals are reported; do not hide with retries that always eventually “pass.”

## Detailed architecture

- [test-strategy.md](./test-strategy.md)
- [contract-testing.md](./contract-testing.md)
- [failure-testing.md](./failure-testing.md)
- [performance-testing.md](./performance-testing.md)

## Phase 1 applicable checks

- Documentation structure script
- Secret pattern script

See `docs/deployment/ci-cd.md`.
