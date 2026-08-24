# AGENTS.md

Rules for AI coding agents working on Nova.

These rules are mandatory. Human contributors should follow the same standards when using AI assistance.

## Mission

Nova is a multi-agent document validation pipeline for trade shipping documents. Agents must improve the repository carefully: preserve contracts, keep changes scoped, and leave documentation accurate.

## Before you modify anything

1. **Inspect before modifying.** Read the relevant source, tests, and docs. Do not edit files you have not inspected.
2. **Understand requirements.** Confirm the user request against `docs/requirements/` and `docs/product/`. If requirements are missing or ambiguous, ask or document assumptions before implementing.
3. **Read architecture docs.** Review [ARCHITECTURE.md](ARCHITECTURE.md), `docs/architecture/`, and any ADRs in `docs/decisions/` that affect the change.
4. **Preserve contracts.** Do not break public APIs, agent interfaces, data schemas, or documented behaviors without an explicit decision and corresponding documentation updates.

## Branching and collaboration

5. **Use feature branches.** Create a dedicated branch for each change set (for example `feat/...`, `fix/...`, `docs/...`).
6. **Never push directly to `main`.** Open a pull request. Do not merge your own PR unless a human explicitly requests it and project policy allows it.

## Implementation standards

7. **Keep changes scoped.** Implement only what was asked. Avoid drive-by refactors and unrelated cleanup.
8. **Avoid modifying unrelated files.** Do not touch files outside the change boundary unless required for correctness (for example, updating a shared type used by the feature).
9. **Do not introduce unnecessary dependencies.** Prefer the existing stack. Add a dependency only when justified, documented, and approved by the change request.
10. **Do not silently alter architecture.** Architectural changes require an ADR update (or a new ADR) and updates to architecture docs. Do not redesign subsystems as a side effect of a feature.

## Tests and honesty

11. **Write tests.** New behavior and bug fixes need automated tests at the appropriate level (unit, integration, evaluation fixtures as applicable).
12. **Run tests.** Execute the relevant test suite before claiming success. If the suite cannot run, say so explicitly.
13. **Report failures honestly.** Surface failing tests, incomplete work, and blocked steps. Do not hide errors.
14. **Do not fabricate results.** Never invent passing tests, metrics, evaluation scores, logs, or “verified” outcomes.

## Documentation

15. **Update documentation.** When behavior, interfaces, configuration, or operations change, update the matching docs under `docs/` and any root overview files.
16. **Update ADRs when architecture changes.** Record decisions in `docs/decisions/` using the ADR template. Link new ADRs from architecture docs when relevant.
17. **Use feature documentation.** New user-facing or system features should follow the [feature template](docs/features/FEATURE_TEMPLATE.md).

## Agent-specific documentation

When adding or changing an agent in the pipeline, document it with the [agent template](docs/agents/AGENT_TEMPLATE.md) under `docs/agents/`.

## Failure and escalation

- If requirements conflict with architecture, stop and escalate; do not guess.
- If a change would touch security-sensitive paths (auth, secrets, PII, document storage), read [SECURITY.md](SECURITY.md) and `docs/security/` first.
- If evaluation quality is affected, update `docs/evaluation/` and note impact in the PR.

## Checklist before opening a PR

- [ ] Inspected affected code and docs
- [ ] Requirements and architecture understood
- [ ] Contracts preserved or intentionally versioned
- [ ] Feature branch used; not targeting a direct push to `main`
- [ ] Tests written and run (or blockers reported)
- [ ] Docs and ADRs updated where needed
- [ ] No unnecessary dependencies
- [ ] Diff limited to the requested scope
- [ ] Status reported honestly

## Related documents

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [DEVELOPMENT.md](DEVELOPMENT.md)
- [TESTING.md](TESTING.md)
- [docs/ai-development/](docs/ai-development/)
- [docs/audits/](docs/audits/)
