# Git rules for AI-assisted development

Git and collaboration rules for AI coding agents on Nova.

## Branching

- Work on a dedicated branch for each change set (`docs/...`, `feat/...`, `fix/...`, `chore/...`).
- Never push directly to `main`.
- Keep branches focused; do not mix unrelated features in one branch.

## Commits

- Commit only when the task requests it, or when completing an authorized end-to-end SDLC run that includes commit.
- Write concise commit messages that explain **why**.
- Do not commit secrets, credentials, or large binary dumps.
- Do not commit generated junk (local caches, virtualenvs, `node_modules`).
- Do not use `--no-verify` or skip hooks unless a human explicitly authorizes it.
- Do not amend commits that were already pushed unless explicitly requested and safe.

## Pull requests

- Push the feature branch and open a PR for review.
- Fill out the PR template honestly (summary, test plan, risks, docs updated).
- Wait for CI and human review before merge.
- Do not merge your own PR unless a human explicitly authorizes it and project policy allows it.
- Do not bypass required CI checks.

## Diff hygiene

- Include only files relevant to the change.
- Do not modify unrelated features.
- Review the diff before committing; remove accidental debug or local-only edits.
- If documentation or tests are required by the change, include them in the same PR.

## Forbidden git behaviors

| Forbidden | Reason |
|-----------|--------|
| Direct push to `main` | Bypasses review and CI |
| Force-push to shared default branches | Destructive / history rewrite risk |
| Fabricating “CI green” claims | Honesty requirement |
| Committing secrets | Security incident risk |
| Hiding failing hooks/CI | Conceals defects |

## Related documents

- [`agent-development-rules.md`](./agent-development-rules.md)
- [`security-rules.md`](./security-rules.md)
- [`review-checklist.md`](./review-checklist.md)
- Root [`CONTRIBUTING.md`](../../CONTRIBUTING.md) (when present)
- `docs/operations/git-workflow.md` (when present)
