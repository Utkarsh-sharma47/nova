# Agent task template

Copy this template when assigning work to an AI coding agent on Nova.

---

## Task title

<!-- Short imperative title, e.g. "Add UNCERTAIN handling to Validator contract docs" -->

## Objective

<!-- One paragraph: what success looks like -->

## Out of scope

<!-- Explicit non-goals. Prevents drive-by implementation -->

-

## Required reading (before coding)

- [ ] [`AGENTS.md`](../../AGENTS.md)
- [ ] [`docs/ai-development/agent-development-rules.md`](./agent-development-rules.md)
- [ ] Requirements: `docs/requirements/…`
- [ ] Architecture: `ARCHITECTURE.md` / `docs/architecture/…`
- [ ] Related ADRs: `docs/decisions/…`
- [ ] Related feature/agent docs: `docs/features/…`, `docs/agents/…`

## Affected components

<!-- Modules, contracts, docs, CI, agents (Extractor / Validator / Router), etc. -->

-

## Implementation plan

1.
2.
3.

## SDLC checklist

- [ ] Inspect repository
- [ ] Read `AGENTS.md` and relevant requirements/architecture
- [ ] Identify affected components
- [ ] Plan smallest correct change
- [ ] Implement
- [ ] Add/update tests
- [ ] Run tests (record commands + results)
- [ ] Run static checks (record commands + results)
- [ ] Review diff
- [ ] Update documentation
- [ ] Report exact verification results
- [ ] Commit
- [ ] Push branch
- [ ] Open PR
- [ ] Wait for CI/review (do not self-merge unless authorized)

## Verification commands

```bash
# Replace with actual commands for this task
```

## Expected documentation updates

- [ ] Feature docs
- [ ] API docs
- [ ] Testing docs
- [ ] Architecture / ADR
- [ ] Evaluation / AI behavior docs
- [ ] N/A — explain:

## AI behavior constraints (if touching Extractor / Validator / Router)

- [ ] Typed contracts
- [ ] Structured output
- [ ] Confidence exposed
- [ ] Evidence preserved
- [ ] Uncertainty respected
- [ ] Bounded retries + timeouts
- [ ] No infinite loops
- [ ] Token/cost tracked
- [ ] No invented values
- [ ] No silent uncertainty → approval

## Risks and rollback

-

## Deliverables

- Branch name:
- PR URL:
- Commit SHAs:
- Verification summary:

## Non-negotiables reminder

Do not fabricate results, bypass CI, commit secrets, push to `main`, self-merge without authorization, hide errors, delete tests to go green, or weaken validation to pass tests.
