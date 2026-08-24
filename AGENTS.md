# AGENTS.md

Mandatory operating rules for AI coding agents working on **Nova**.

Nova is a multi-agent AI pipeline for trade/shipping document verification (Extractor → Validator → Router → persistence → query/UI). Treat it as an operational system, not a prototype chatbot.

Human contributors using AI assistance must follow the same standards.

---

## AI coding SDLC (mandatory)

Every AI coding agent must follow this sequence:

1. Inspect repository.
2. Read this `AGENTS.md`.
3. Read relevant requirements (`docs/requirements/`, `docs/product/`).
4. Read architecture documentation (`ARCHITECTURE.md`, `docs/architecture/`, relevant ADRs in `docs/decisions/`).
5. Identify affected components.
6. Plan implementation.
7. Implement the **smallest correct change**.
8. Add or update tests.
9. Run tests.
10. Run static checks.
11. Review the diff.
12. Update documentation.
13. Report **exact** verification results.
14. Commit.
15. Push the branch.
16. Open a pull request.
17. Wait for CI and human review before merge.

If a step cannot be completed (for example application tests do not exist yet in Phase 1), state that explicitly. Do **not** claim it passed.

Detailed agent process: [`docs/ai-development/agent-development-rules.md`](docs/ai-development/agent-development-rules.md)

Task intake template: [`docs/ai-development/agent-task-template.md`](docs/ai-development/agent-task-template.md)

---

## Non-negotiable rules

Agents must **never**:

- Fabricate test results, metrics, evaluation scores, or logs
- Claim success without verification actually performed
- Silently change architecture, contracts, or stage boundaries
- Bypass CI
- Commit secrets or credentials
- Modify unrelated features
- Delete tests merely to make CI pass
- Weaken validation or assertions to make a test pass
- Hardcode production credentials
- Push directly to `main`
- Merge their own PR unless a human explicitly authorizes it
- Hide errors
- Suppress failing command output

Additional coding, testing, security, and git rules live under [`docs/ai-development/`](docs/ai-development/).

---

## Documentation rule

Every meaningful feature must update, as applicable:

- Feature documentation (`docs/features/`)
- API documentation (`docs/api/`) if interfaces change
- Testing documentation (`docs/testing/`) if behavior changes
- Architecture docs and/or ADR (`docs/architecture/`, `docs/decisions/`) if architecture changes
- Evaluation documentation (`docs/evaluation/`) if AI behavior changes

See [`docs/ai-development/documentation-rules.md`](docs/ai-development/documentation-rules.md).

---

## Runtime AI agents (Extractor, Validator, Router)

Future AI agents implementing Extractor, Validator, and Router must:

- Use typed contracts
- Produce structured output
- Expose confidence
- Preserve evidence
- Respect uncertainty
- Have bounded retries
- Have timeout handling
- Avoid infinite loops
- Track token/cost usage
- Never invent unavailable values
- Never silently convert uncertainty into approval (`AUTO_APPROVE` / false `MATCH`)

See [`docs/ai-development/agent-development-rules.md`](docs/ai-development/agent-development-rules.md) and [`docs/ai-development/architecture-rules.md`](docs/ai-development/architecture-rules.md).

---

## Scope and architecture discipline

- Implement only what was asked; prefer minimal diffs.
- Do not introduce unnecessary dependencies.
- Do not redesign subsystems as a side effect of a feature.
- Architectural changes require ADR + architecture doc updates.
- Preserve Part 2 extension points; do not implement Part 2 unless explicitly tasked.

---

## Security (summary)

- No secrets in git, logs, fixtures, or examples (placeholders only).
- Treat shipping documents and extracted fields as sensitive.
- Validate model output against schemas before downstream use.
- Read `SECURITY.md` and `docs/security/` before changing auth, secrets, PII, or document storage paths.

Full rules: [`docs/ai-development/security-rules.md`](docs/ai-development/security-rules.md)

---

## Git and PR (summary)

- Use a dedicated feature/docs branch.
- Never push to `main`.
- Open a PR; wait for CI and human review.
- Do not self-merge unless explicitly authorized.

Full rules: [`docs/ai-development/git-rules.md`](docs/ai-development/git-rules.md)

---

## Human review

Reviewers of AI-generated changes must use:

[`docs/ai-development/review-checklist.md`](docs/ai-development/review-checklist.md)

Coverage includes architecture, correctness, tests, security, observability, AI behavior, prompt changes, cost, latency, failure handling, documentation, and regression risk.

---

## Governance index (`docs/ai-development/`)

| Document | Purpose |
|----------|---------|
| [agent-development-rules.md](docs/ai-development/agent-development-rules.md) | SDLC + runtime agent rules |
| [coding-rules.md](docs/ai-development/coding-rules.md) | Code quality and change hygiene |
| [testing-rules.md](docs/ai-development/testing-rules.md) | Tests, CI honesty, static checks |
| [documentation-rules.md](docs/ai-development/documentation-rules.md) | Required doc updates |
| [architecture-rules.md](docs/ai-development/architecture-rules.md) | Architecture and contracts |
| [security-rules.md](docs/ai-development/security-rules.md) | Secrets, PII, model safety |
| [git-rules.md](docs/ai-development/git-rules.md) | Branches, commits, PRs |
| [review-checklist.md](docs/ai-development/review-checklist.md) | Human review of AI PRs |
| [agent-task-template.md](docs/ai-development/agent-task-template.md) | Task assignment template |

---

## Before opening a PR

- [ ] Inspected affected code and docs
- [ ] Requirements and architecture understood
- [ ] Smallest correct change implemented
- [ ] Tests added/updated and run (or blockers reported honestly)
- [ ] Static checks run (or absence explained)
- [ ] Diff reviewed; unrelated changes excluded
- [ ] Documentation updated per the documentation rule
- [ ] Exact verification results reported
- [ ] Feature branch used; not a direct `main` push
- [ ] No secrets in the diff
