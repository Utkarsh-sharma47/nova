# Continuous Integration

Nova CI is intentionally staged. Phase 1 only runs checks that are valid for the
current repository. Application lint/test/build jobs are added when those stacks exist.

## Triggers

`.github/workflows/ci.yml` runs on:

- every `pull_request`
- every `push` to `main`

## Phase 1 jobs

| Job | What it does | Failure behavior |
|-----|--------------|------------------|
| Repository hygiene | Runs `scripts/check-docs-structure.sh` | Job fails; PR cannot merge if required |
| Secret pattern scan | Runs `scripts/check-secret-patterns.sh` | Job fails on heuristic matches |
| Gitleaks | Scans the repository with a pinned Gitleaks release | Job fails on detected leaks |

Quality rules:

- Required checks must fail the workflow when they fail.
- Do not use `|| true` (or equivalent) to force green builds.
- Do not add fake commands (`pytest`, `npm test`, etc.) before those tools exist.
- Prefer pinned action / tool versions.
- Use readable job names.
- Cache package managers when Python/Node jobs are introduced.

## Extending CI in later phases

Add jobs to the same workflow (or a focused workflow under `.github/workflows/`)
only when the corresponding project files exist.

### Python backend (when present)

Gate on files such as `pyproject.toml` / `requirements.txt` and configs for Ruff/MyPy.

Suggested jobs:

1. **Ruff** — lint (and format check when configured)
2. **MyPy** — type checking against the declared package set
3. **pytest** — unit/integration tests with a real test suite

Use `actions/setup-python` with pip/poetry/uv caching. Install from the lockfile or
declared dependency set. Do not invent a test command if no tests exist yet.

Example condition pattern:

```yaml
python-checks:
  name: Python checks
  if: hashFiles('pyproject.toml', 'requirements.txt') != ''
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4.2.2
    - uses: actions/setup-python@v5.3.0
      with:
        python-version: "3.12"
        cache: pip
    # Install and run ruff / mypy / pytest only after those tools are configured.
```

### Frontend (when present)

Gate on `package.json` (and lockfile).

Suggested jobs:

1. **ESLint**
2. **TypeScript** (`tsc --noEmit` or project equivalent)
3. **Build** (production build)

Use `actions/setup-node` with npm/pnpm/yarn caching from the lockfile.

### Repository / docs (ongoing)

Keep Phase 1 hygiene and secret scanning. Expand documentation checks when the
`docs/` tree and link conventions stabilize (for example markdown lint or link check).

### Evaluation / agents / database (future)

Add dedicated jobs only after harnesses and services exist:

- evaluation fixture runs
- migration checks
- smoke tests against ephemeral services

Document new jobs in [DEVELOPMENT.md](../../DEVELOPMENT.md) when they become local commands.

## Branch protection (manual GitHub setting)

Repository admins should require these checks on `main`:

- Repository hygiene
- Secret pattern scan
- Gitleaks

Disallow direct pushes to `main`. Require a PR and an up-to-date branch before merge.
See [CONTRIBUTING.md](../../CONTRIBUTING.md).
