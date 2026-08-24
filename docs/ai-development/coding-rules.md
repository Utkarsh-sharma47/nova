# Coding rules for AI-assisted development

Standards for code produced or modified by AI coding agents on Nova.

## General

- Match existing project style, naming, and layout when application code exists.
- Prefer clarity and explicitness over cleverness.
- Keep functions and modules focused; avoid unrelated responsibilities in one change.
- Do not leave dead code, commented-out experiments, or temporary debug hooks in commits.
- Do not add dependencies unless justified by the task, compatible with project standards, and documented.

## Contracts and types

- Prefer typed interfaces for public APIs, agent I/O, persistence models, and router decisions.
- Do not weaken types or validation to satisfy a failing test.
- Backward-incompatible contract changes require documentation and, when architectural, an ADR.
- Structured agent outputs must validate against their schemas before downstream use.

## Error handling

- Fail explicitly: return typed errors or raise expected exceptions; do not swallow failures.
- Do not catch-and-ignore exceptions to force a green path.
- Timeouts, retries, and cancellation must be intentional and bounded.
- User-facing and ops-facing errors must not leak secrets or raw credentials.

## Configuration and secrets

- Configuration via environment or approved config mechanisms—never hardcode production credentials.
- Secrets stay out of source, logs, fixtures, and commit history.
- Provide examples only as placeholders (for example `.env.example`), never real values.

## AI / LLM integration (when implemented)

- Prompts and model parameters that affect behavior are versioned and documented.
- Model calls must record enough metadata for cost, latency, and failure analysis (without logging sensitive document contents beyond policy).
- Do not invent field values when extraction fails or confidence is low.
- Uncertainty must propagate to Validator and Router—not be normalized away.

## Scope of edits

- Change only files required for the task.
- Avoid drive-by formatting of untouched files.
- Do not delete or disable tests, linters, or CI gates to obtain a pass.
- Do not bypass CI locally or in the PR process.

## Phase 1 note

Phase 1 establishes documentation and engineering foundation. Application modules may not exist yet. Coding agents must not invent application scaffolding unless the task explicitly requests it.

## Related documents

- [`agent-development-rules.md`](./agent-development-rules.md)
- [`architecture-rules.md`](./architecture-rules.md)
- [`security-rules.md`](./security-rules.md)
- [`testing-rules.md`](./testing-rules.md)
