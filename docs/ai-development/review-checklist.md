# Human review checklist for AI-generated changes

Use this checklist when reviewing pull requests produced or heavily assisted by AI coding agents.

Mark each item **Pass**, **Fail**, or **N/A**. Failures block merge unless explicitly waived with rationale.

## Architecture

- [ ] Change respects documented stage boundaries and contracts.
- [ ] No silent architecture redesign; ADRs updated if architecture changed.
- [ ] Part 2 extension points not broken by Part 1 shortcuts.
- [ ] New dependencies / infrastructure justified and documented.

## Correctness

- [ ] Implements the requested behavior only; no unrelated feature drift.
- [ ] Edge cases for missing data, mismatches, and uncertainty handled.
- [ ] Error paths are explicit; failures are not swallowed.
- [ ] Assumptions are stated in the PR or docs.

## Tests

- [ ] Tests added/updated for the change.
- [ ] Relevant tests were actually run; results reported honestly.
- [ ] No tests deleted or skipped solely to pass CI.
- [ ] Validation/assertions not weakened solely to pass tests.
- [ ] Static checks run (or absence explained).

## Security

- [ ] No secrets, credentials, or private keys in the diff.
- [ ] No hardcoded production credentials.
- [ ] Sensitive document/PII handling remains appropriate.
- [ ] Model/tool outputs treated as untrusted and schema-validated.
- [ ] CI security / secret checks not bypassed.

## Observability

- [ ] Sufficient logging/metrics/traces for failures and key decisions (when runtime code exists).
- [ ] Logs avoid leaking secrets and unnecessary sensitive payloads.
- [ ] Decision outcomes (validation + routing) are auditable.

## AI behavior

- [ ] Typed contracts and structured outputs preserved.
- [ ] Confidence exposed where extraction/validation requires it.
- [ ] Evidence preserved and linked to source material.
- [ ] Uncertainty respected; not coerced into false certainty.
- [ ] Unavailable values not invented.

## Prompt changes

- [ ] Prompt/policy changes are intentional, versioned, and documented.
- [ ] Behavioral impact described in the PR.
- [ ] Evaluation docs updated if AI behavior changed.

## Cost

- [ ] Token/cost implications considered for new or heavier model calls.
- [ ] Cost/token tracking retained or added where applicable.
- [ ] No unbounded retry storms that amplify cost.

## Latency

- [ ] Timeouts present for model/tool/network calls.
- [ ] No obvious unnecessary serial model calls introduced without justification.
- [ ] Latency impact noted for user-facing or pipeline-critical paths.

## Failure handling

- [ ] Bounded retries; no infinite loops.
- [ ] Timeout and cancellation behavior defined.
- [ ] Failures surface to operators/UI appropriately.
- [ ] Uncertainty never silently converts into `AUTO_APPROVE`.

## Documentation

- [ ] Feature / API / testing / architecture / evaluation docs updated as required.
- [ ] `AGENTS.md` / `docs/ai-development/` still accurate if process changed.
- [ ] README or contributor docs updated if workflow entry points changed.

## Regression risk

- [ ] Diff scoped; unrelated modules untouched.
- [ ] Existing acceptance criteria still held.
- [ ] Known fragile areas (routing thresholds, schema migrations, auth) explicitly reviewed.
- [ ] Rollback / feature-flag considerations noted when risk is high.

## Reviewer sign-off

| Field | Value |
|-------|-------|
| PR | |
| Reviewer | |
| Date | |
| Verdict | Approve / Request changes / Reject |
| Waivers (if any) | |
