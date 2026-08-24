# CI/CD foundation

## Current repository reality (Phase 1)

The repository contains **documentation and governance files only**. There is no application stack yet (no Python/Node package manifests, no app lint/type/build targets).

Therefore CI must **not** invent fake `npm test` / `pytest` / linter steps that always succeed or that fail because tools do not exist.

## Phase 1 CI jobs (enforced)

| Check | Script / action | Fails when |
|-------|-----------------|------------|
| Docs structure | `scripts/check-docs-structure.sh` | Required docs paths missing |
| Secret patterns | `scripts/check-secret-patterns.sh` | High-confidence secret patterns found in tracked files |

Workflow: `.github/workflows/ci.yml`

## Deferred CI (enable when stack exists)

Documented here so future agents do not skip them:

| Check | Prerequisite |
|-------|--------------|
| Formatting / linting | Language toolchain chosen + config committed |
| Static analysis | Same |
| Type checking | Typed codebase exists |
| Unit/integration tests | Application tests exist |
| Build validation | Buildable app package exists |
| Docs link/consistency extras | Optional once docs grow |

## Rules

1. CI must fail correctly on real problems.
2. No success-only placeholder steps.
3. Expanding CI is done in the same PR (or immediate follow-up) that introduces the toolchain.
4. Never bypass CI to merge broken mainline.

## Local run

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
```
