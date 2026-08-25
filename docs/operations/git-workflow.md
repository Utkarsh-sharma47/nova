# Git workflow

## Branch model

```text
main
  ├── feature/*
  ├── fix/*
  ├── docs/*
  ├── test/*
  └── chore/*
```

Simple branch-and-PR model. No GitFlow release branches required for this assignment.

## Rules

1. **`main` is protected conceptually** — no direct development commits on `main`.
2. Every change happens on a branch starting from **latest `main`**.
3. Pull/sync latest `main` before branching.
4. Commit logically with conventional types.
5. Push the branch to `origin`.
6. Open a PR.
7. **CI must pass**.
8. Review the diff (human and/or AI review as available).
9. Merge only after checks pass.
10. After merge, sync local `main` and delete the merged branch when appropriate.

**Note:** GitHub branch protection was not enabled on `main` at Phase 1 reconnaissance. Maintainers should enable required PR + CI checks when possible. Until then, the team still follows this workflow by policy (`AGENTS.md`, `CONTRIBUTING.md`).

## Conventional commit types

| Type | Use |
|------|-----|
| `feat:` | New user-facing capability |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `test:` | Tests only |
| `refactor:` | Code change without behavior change |
| `perf:` | Performance improvement |
| `chore:` | Maintenance, tooling, housekeeping |
| `ci:` | CI configuration |

Examples:

```text
docs: add Phase 1 requirements inventory
ci: add docs structure and secret pattern checks
feat: add extractor agent contract tests
```

## PR expectations

- Link `REQ-*` IDs when implementing requirements
- Keep PRs focused
- Update docs/ADRs when behavior or architecture changes
- Do not include secrets

## AI agents

AI coding agents must follow this workflow and must not push directly to `main`. See `AGENTS.md`.
