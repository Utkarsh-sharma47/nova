# AI agent development rules

Rules for AI coding agents that change Nova, and for future runtime agents (Extractor, Validator, Router).

## Mandatory pre-work

Before any code or documentation change:

1. Inspect the repository structure and relevant files.
2. Read [`AGENTS.md`](../../AGENTS.md).
3. Read relevant requirements under `docs/requirements/` and product docs under `docs/product/`.
4. Read architecture documentation (`ARCHITECTURE.md`, `docs/architecture/`, relevant ADRs in `docs/decisions/`).
5. Identify affected components, contracts, and docs.
6. Plan the smallest correct change.

Do not implement until steps 1–6 are complete enough to justify the change.

## AI coding SDLC

Every AI coding agent must follow this sequence:

1. Inspect repository.
2. Read `AGENTS.md`.
3. Read relevant requirements.
4. Read architecture documentation.
5. Identify affected components.
6. Plan implementation.
7. Implement the smallest correct change.
8. Add or update tests.
9. Run tests.
10. Run static checks.
11. Review the diff.
12. Update documentation.
13. Report exact verification results.
14. Commit.
15. Push the branch.
16. Open a pull request.
17. Wait for CI and human review before merge.

Skipping steps is not allowed. If a step cannot be completed (for example tests are not yet available in Phase 1), say so explicitly and do not claim it passed.

## Scope discipline

- Implement only the requested work.
- Prefer the smallest correct change over broad refactors.
- Do not modify unrelated features or files.
- Do not “clean up” surrounding code unless required for correctness.
- Do not silently change architecture, contracts, schemas, or routing behavior.

## Honesty and verification

- Never fabricate test results, metrics, evaluation scores, or logs.
- Never claim success without verification you actually ran.
- Report exact commands and outcomes (pass/fail, exit codes, notable errors).
- Never hide errors or suppress failing command output.
- If blocked, state the blocker and stop rather than inventing progress.

## Runtime AI agents (Extractor, Validator, Router)

When implementing or changing Nova’s pipeline agents, the agent must:

| Rule | Requirement |
|------|-------------|
| Typed contracts | Inputs and outputs use explicit typed schemas/contracts. |
| Structured output | Prefer structured, machine-parseable results over free-form prose. |
| Confidence | Expose confidence (or equivalent uncertainty signal) for extracted/validated fields. |
| Evidence | Preserve evidence linking values to source spans, pages, or artifacts. |
| Uncertainty | Respect uncertainty; do not coerce unknowns into false certainty. |
| Bounded retries | Retries are finite and explicit; no unbounded retry loops. |
| Timeouts | Every external/model call has timeout handling. |
| No infinite loops | Control flow must terminate; loops need hard bounds. |
| Cost tracking | Track token/cost usage for model calls where applicable. |
| No invention | Never invent unavailable values; use explicit missing/uncertain states. |
| No silent approval | Never silently convert uncertainty into `MATCH` / `AUTO_APPROVE`. |

Routing decisions (`AUTO_APPROVE`, `HUMAN_REVIEW`, `AMENDMENT_REQUEST`) must remain auditable and grounded in validation outcomes plus documented policy—not model improvisation.

## Escalation

Stop and escalate when:

- Requirements conflict with architecture or ADRs.
- A change would weaken validation, security, or evaluation integrity to “make CI pass.”
- Required documentation or contracts are missing and cannot be inferred safely.

## Related documents

- [`coding-rules.md`](./coding-rules.md)
- [`testing-rules.md`](./testing-rules.md)
- [`architecture-rules.md`](./architecture-rules.md)
- [`security-rules.md`](./security-rules.md)
- [`git-rules.md`](./git-rules.md)
- [`review-checklist.md`](./review-checklist.md)
- [`agent-task-template.md`](./agent-task-template.md)
