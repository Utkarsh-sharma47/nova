# Testing

Detailed testing documentation for Nova. Overview: [TESTING.md](../../TESTING.md).

## Purpose

Define suites, fixtures, naming conventions, and CI expectations as the codebase grows.

## Current status

No automated suite yet. Establish conventions here when the first tests land.

## Planned contents

| Topic | Status |
|-------|--------|
| Suite layout and naming | Planned |
| Fixture policy | Planned |
| CI gates | Planned |
| Contract test catalog | Planned |

## Principles

- Tests must be runnable and honest; never fabricate results.
- Prefer deterministic fixtures; isolate flaky model-dependent checks under evaluation where appropriate.
- Document how to run each suite in [DEVELOPMENT.md](../../DEVELOPMENT.md) when commands exist.

## Related

- [TESTING.md](../../TESTING.md)
- [Evaluation](../evaluation/)
- [AGENTS.md](../../AGENTS.md)
