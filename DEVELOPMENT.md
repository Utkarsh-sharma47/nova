# Development

Local development guidance for Nova.

## Current status

Application code and a concrete toolchain are not yet established. This document defines the intended development process. Concrete setup commands will be added when the stack is chosen and recorded in ADRs.

## Prerequisites (to be finalized)

When implementation begins, this section will list:

- Required language runtimes and versions
- Package managers
- Optional local services (for example databases or queues), if any
- How to obtain sample documents for development (without real customer PII)

Do not assume a stack until it is decided and documented.

## Repository layout (documentation phase)

```
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
└── docs/
```

Application source directories will be documented here when introduced.

## Branching

- Branch from `main`.
- Use descriptive prefixes: `feat/`, `fix/`, `docs/`, `chore/`, `test/`.
- Never push commits directly to `main`.

## Making changes

1. Read requirements and architecture docs for the area you touch.
2. Keep changes scoped to the task.
3. Add or update tests with the change.
4. Update documentation in the matching `docs/` section.
5. If architecture changes, add or update an ADR.

## Running the project

Not yet applicable. Commands for install, run, migrate, and lint will be added when the application skeleton exists.

## Environment configuration

Secrets and environment variable conventions will be documented under `docs/deployment/` and `docs/security/` when configuration is introduced. Do not commit secrets.

## Related documents

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [TESTING.md](TESTING.md)
- [docs/ai-development/](docs/ai-development/)
- [docs/deployment/](docs/deployment/)
