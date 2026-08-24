# Development

Local development workflow for Nova. Phase 1 is repository and CI foundation only — no application packages yet.

## Prerequisites

- Git 2.40+
- A GitHub account with access to this repository
- Bash (for Phase 1 check scripts)

Optional later (not required for Phase 1):

- Python 3.11+ and tooling (Ruff, MyPy, pytest) when the backend exists
- Node.js LTS and package manager when the frontend exists

## Clone and branch

```bash
git clone https://github.com/Utkarsh-sharma47/nova.git
cd nova
git checkout main
git pull origin main
git checkout -b feature/your-change   # or fix/, docs/, ci/, etc.
```

Follow the branch model in [CONTRIBUTING.md](CONTRIBUTING.md).

## Environment and secrets

```bash
cp .env.example .env
# Edit .env locally. Never commit it.
```

`.env`, `*.env`, credential files, and private keys are gitignored. See [SECURITY.md](SECURITY.md).

## Phase 1 local checks

These are the only automated checks that apply until application code exists:

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
```

Both scripts exit non-zero on failure. Do not ignore failures.

## What CI runs today

On every `pull_request` and every `push` to `main`, GitHub Actions runs:

| Job | Purpose |
|-----|---------|
| Repository hygiene | Required foundation files + docs structure script |
| Secret pattern scan | Heuristic scan via `scripts/check-secret-patterns.sh` |
| Gitleaks | Full-repo secret detection |

See `.github/workflows/ci.yml` and [docs/deployment/ci-cd.md](docs/deployment/ci-cd.md).

## Day-to-day loop

1. Sync `main` and create a focused branch.
2. Make the smallest change that satisfies the task.
3. Run Phase 1 local checks (and app checks when they exist).
4. Commit with a conventional message.
5. Push the branch and open a PR to `main`.
6. Wait for CI; fix failures; keep the branch synchronized with `main` before merge.

## When application code arrives

Do **not** invent commands that the repo cannot run. After backend/frontend land:

| Area | Expected local commands (when configured) |
|------|-------------------------------------------|
| Python | `ruff check`, `mypy`, `pytest` |
| Frontend | `eslint`, `tsc --noEmit`, production `build` |

Exact package managers and config files will be documented in this file when those stacks are added. Until then, CI must not pretend they exist.

## Extending CI

How to grow CI without breaking Phase 1 is documented in [docs/deployment/ci-cd.md](docs/deployment/ci-cd.md).
