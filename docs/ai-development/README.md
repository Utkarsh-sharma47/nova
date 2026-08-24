# AI development

Guidance for AI-assisted development on Nova.

## Purpose

Nova is expected to be built with substantial AI coding agent assistance. This section complements [AGENTS.md](../../AGENTS.md) with workflow practices specific to this repository.

## Mandatory rules

Follow [AGENTS.md](../../AGENTS.md) in full. Highlights:

- Inspect before modifying; understand requirements; read architecture docs.
- Preserve contracts; keep changes scoped; avoid unrelated files.
- Use feature branches; never push directly to `main`.
- Write and run tests; report failures honestly; never fabricate results.
- Update documentation and ADRs when architecture or behavior changes.
- Do not introduce unnecessary dependencies or silently alter architecture.

## Recommended workflow for agents

1. Restate the task and identify affected docs (`requirements`, `architecture`, `agents`, `features`).
2. Inspect existing files; list what will change before editing.
3. Implement the smallest coherent change.
4. Update docs/templates/ADRs as needed.
5. Run tests (or document why they cannot run).
6. Summarize residual risks and open questions.

## Documentation expectations

| Change type | Update |
|-------------|--------|
| New feature | Feature doc from template |
| New/changed agent | Agent doc from template |
| Architecture shift | ADR + architecture docs |
| Quality methodology | Evaluation docs |
| Security control | Security docs |

## Related

- [AGENTS.md](../../AGENTS.md)
- [CONTRIBUTING.md](../../CONTRIBUTING.md)
- [Audits](../audits/)
