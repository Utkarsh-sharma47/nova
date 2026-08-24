# Engineering standards

## Contracts

- Publish JSON Schema / typed models for agent I/O and API payloads when code exists.
- Reject invalid payloads at boundaries; do not “best effort” corrupt data into persistence.

## Code quality (when application code exists)

- Prefer clear modules along pipeline stages over a single monolith script.
- No secrets in source; configuration via environment with `.env.example`.
- Dependency versions pinned via lockfiles once a stack is chosen.
- Public functions handling money/dates/identifiers must have explicit parsing rules.

## Git

- Follow `docs/operations/git-workflow.md`.
- Conventional commits; focused PRs.
- Do not push to `main`; do not bypass CI.

## Documentation

- Update feature/agent docs with behavior changes.
- Add/update ADRs for architectural decisions.

## AI-assisted development

- Obey `AGENTS.md` and `docs/ai-development/governance.md`.
- Never fabricate test results.

## Error handling

- Classify errors (validation, extraction, timeout, provider, persistence).
- Bounded retries with jitter where appropriate; then fail safe.

## Performance / cost

- Avoid unnecessary multi-pass LLM calls in Part 1 demos.
- Record cost metrics for LLM stages when implemented.
