# Development

Local development guidance for Nova.

## Current status

Application code and a concrete toolchain are not yet established. Concrete setup commands will be added when the stack is chosen and recorded in ADRs.

## Phase 1 local checks

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
```

These are the only automated checks until application tooling exists. See [`docs/deployment/ci-cd.md`](docs/deployment/ci-cd.md).

## Prerequisites (to be finalized in Phase 2)

When implementation begins, this section will list:

- Required language runtimes and versions
- Package managers
- Optional local services (databases/queues), if any
- How to obtain sample documents (no real customer PII)

## Repository layout (Phase 1)

```text
.
├── AGENTS.md
├── ARCHITECTURE.md
├── CONTRIBUTING.md
├── DEVELOPMENT.md
├── README.md
├── ROADMAP.md
├── SECURITY.md
├── TESTING.md
├── CHANGELOG.md
├── .env.example
├── .gitignore
├── .github/workflows/ci.yml
├── scripts/
└── docs/
```

## Branching

Follow [`docs/operations/git-workflow.md`](docs/operations/git-workflow.md):

- Branch from latest `main`
- Prefixes: `feature/`, `fix/`, `docs/`, `test/`, `chore/`
- Never push directly to `main`

## Making changes

1. Read `AGENTS.md` and relevant requirements/architecture docs.
2. Keep changes scoped; cite `REQ-*` when applicable.
3. Add or update tests with application changes (when code exists).
4. Update documentation in the matching `docs/` section.
5. If architecture changes, add or update an ADR.

## Environment configuration

Use `.env.example` as a template. Never commit secrets. See [`docs/security/baseline.md`](docs/security/baseline.md).

## Related documents

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [TESTING.md](TESTING.md)
- [docs/ai-development/](docs/ai-development/)
- [docs/deployment/](docs/deployment/)
