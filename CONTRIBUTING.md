# Contributing to Nova

This document defines the Git workflow and contribution standards for Nova.

## Branch model

| Branch | Purpose |
|--------|---------|
| `main` | Protected integration branch. Always releasable foundation. |
| `feature/*` | New capabilities and product work |
| `fix/*` | Bug fixes |
| `docs/*` | Documentation-only changes |
| `test/*` | Test harnesses, fixtures, evaluation scaffolding |
| `chore/*` | Maintenance, dependency hygiene, repo cleanup |
| `ci/*` | CI/CD and repository infrastructure |

Examples: `feature/document-ingestion`, `fix/router-edge-case`, `docs/phase-1-foundation`, `ci/phase-1-foundation`.

## Rules

1. **No direct development on `main`.** Create a dedicated branch for every change. Do not push commits straight to `main`.
2. **Start from latest `main`.** Before branching:
   ```bash
   git fetch origin
   git checkout main
   git pull origin main
   git checkout -b feature/your-change
   ```
3. **Focused commits.** One logical change per commit. Do not mix unrelated refactors with feature work.
4. **Conventional commits.** Use [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   <type>(optional-scope): <short summary>

   [optional body]
   ```
   Common types: `feat`, `fix`, `docs`, `test`, `chore`, `ci`, `refactor`, `perf`, `build`.
5. **PR-based integration.** Open a pull request into `main`. Describe what changed, why, how it was verified, and any risks.
6. **CI must pass before merge.** Required checks on the PR must be green. Do not merge with failing workflows.
7. **Synchronize before merge.** Rebase or merge latest `main` into your branch so the PR is up to date:
   ```bash
   git fetch origin
   git rebase origin/main
   # or: git merge origin/main
   ```
8. **No secrets.** Never commit `.env`, API keys, tokens, private keys, or credential files. See [SECURITY.md](SECURITY.md).
9. **No generated junk.** Do not commit `node_modules/`, virtualenvs, build artifacts, caches, logs, or local IDE files. Rely on `.gitignore`.

## Pull request checklist

- [ ] Branch named per the model above, started from latest `main`
- [ ] Commits are focused and use conventional messages
- [ ] CI is green
- [ ] Branch is synchronized with `main`
- [ ] No secrets or generated artifacts included
- [ ] Docs updated when behavior or process changes
- [ ] Scope matches the PR title (no drive-by changes)

## What belongs where

- Application code → later phases (`feature/*`, `fix/*`)
- Documentation system → `docs/*`
- Repository / CI infrastructure → `ci/*`
- Tests and evaluation harnesses → `test/*`

## Local verification

See [DEVELOPMENT.md](DEVELOPMENT.md) for local setup and Phase 1 checks.

## Questions

If requirements or architecture are unclear, ask before implementing. Prefer small, reviewable PRs.
