# AI development governance

Applies to Claude Code, Cursor, Codex, and any other coding agent.

## Mandatory pre-change reads

1. `AGENTS.md`
2. Relevant files under `docs/architecture/`
3. Relevant files under `docs/features/` and `docs/agents/` (when present)
4. Matching `REQ-*` rows in `docs/requirements/inventory.md`

## Mandatory behaviors

1. Respect existing contracts; no silent architecture changes.
2. Add tests for implementation changes (once app code exists).
3. Update documentation when behavior changes.
4. Run applicable checks before claiming completion.
5. Report failed tests honestly; never fabricate results.
6. Never commit secrets; never bypass CI; never push to `main`.
7. Use feature branches; keep commits focused.
8. Explain significant architectural changes; update ADRs.

## Phase discipline

- Do not implement later-phase application features during foundation-only work unless a human explicitly expands scope **and** docs/roadmap are updated first.
- Do not create fake application tests to make CI look mature.
- Do not add language toolchains “just in case.”

## Architecture change protocol

1. Describe the change in the PR.
2. Add or amend an ADR in `docs/decisions/`.
3. Update principles/extension-point docs if impacted.
4. Update inventory/traceability if requirements shift.

## Definition of done (agent)

A task is done only when:

- Code/docs changes match the requested scope
- Applicable scripts/CI pass
- Docs updated
- Limitations and follow-ups stated honestly
