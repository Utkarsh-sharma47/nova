# Contributing to Nova

Thank you for contributing. Nova is developed as a production-quality operational system. Read this before opening a PR.

## Before you start

1. Read [`AGENTS.md`](./AGENTS.md) (also required for AI coding agents).
2. Read [`docs/operations/git-workflow.md`](./docs/operations/git-workflow.md).
3. Confirm the change belongs to the current roadmap phase (`docs/roadmap/roadmap.md`).
4. For requirement-facing work, locate the `REQ-*` ID in `docs/requirements/inventory.md`.

## Workflow (short)

```text
main (protected conceptually)
  └── feature/* | fix/* | docs/* | test/* | chore/*
```

1. Sync latest `main`.
2. Create a branch with the correct prefix.
3. Make focused commits using conventional types (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `perf:`, `chore:`, `ci:`).
4. Push the branch and open a PR.
5. Ensure CI passes.
6. Merge only after checks pass; then sync local `main` and delete the merged branch.

Do **not** push directly to `main`. Do **not** bypass hooks or CI.

## Documentation

Behavior changes require documentation updates. See the checklist in `AGENTS.md`.

## Tests

- Do not invent fake application tests for code that does not exist.
- When application code exists, every behavior change must include tests.
- Report failures honestly; never fabricate results.

## Secrets

Never commit `.env` files, API keys, or credentials. Use `.env.example` with placeholders only.
