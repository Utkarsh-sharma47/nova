# Testing rules for AI-assisted development

Rules for how AI coding agents write, run, and report tests for Nova.

## Mandatory behavior

- Add or update tests for new behavior and bug fixes.
- Run the relevant tests before claiming success.
- Run static checks (lint, typecheck, format, security scans) when they exist for the change.
- Report **exact** verification results: commands run, pass/fail, and material failures.
- Never fabricate test results or claim tests passed without running them.
- Never delete, skip, or weaken tests merely to make CI pass.
- Never weaken production validation or assertions solely to make a test pass.

## What to test (when application code exists)

| Layer | Expectations |
|-------|----------------|
| Unit | Pure logic, parsers, rule evaluation, routing policy helpers |
| Contract | Agent I/O schemas, API request/response shapes |
| Integration | Pipeline stages wired together with fixtures |
| Evaluation | Extraction/validation quality fixtures under `docs/evaluation/` guidance |
| Regression | Previously fixed failure cases remain covered |

## AI pipeline–specific expectations

- Extraction tests must cover missing fields, low confidence, and evidence preservation.
- Validation tests must cover `MATCH`, `MISMATCH`, and `UNCERTAIN`—not only happy paths.
- Router tests must show that uncertainty does not silently become `AUTO_APPROVE`.
- Timeout and bounded-retry behavior should be tested where implemented.
- Cost/token accounting hooks, when present, should be covered at least at unit level.

## Honesty under incomplete tooling

During Phase 1 (docs-only foundation), application test suites may not exist.

Agents must:

- State clearly that application tests are not available yet, if that is the case.
- Still validate documentation structure and any existing CI checks that apply.
- Not invent “all tests passed” narratives.

## CI

- Do not bypass CI.
- Do not mark checks as success without evidence.
- If CI fails, fix the cause or document the blocker; do not disable the check without explicit authorization.

## Related documents

- [`agent-development-rules.md`](./agent-development-rules.md)
- [`review-checklist.md`](./review-checklist.md)
- Root [`TESTING.md`](../../TESTING.md) (when present)
- [`docs/testing/test-strategy.md`](../testing/test-strategy.md)
- [`docs/evaluation/evaluation-framework.md`](../evaluation/evaluation-framework.md)
- [`docs/evaluation/regression-policy.md`](../evaluation/regression-policy.md)
