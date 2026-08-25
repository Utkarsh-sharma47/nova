# Architecture rules for AI-assisted development

Rules that keep Nova’s architecture stable under AI-driven changes.

## Core principles

- Nova is an operational verification system for trade/shipping documents—not a generic chatbot.
- Prefer explicit stage boundaries: ingestion → extraction → validation → routing → persistence → query/UI.
- Preserve Part 2 extension points without implementing Part 2 early.
- Prefer typed contracts between stages over ad-hoc string passing.
- Prefer auditable decisions over opaque model improvisation.

## Non-negotiable architecture constraints

AI coding agents must never:

- Silently change architecture, stage boundaries, or ownership of responsibilities.
- Collapse Extractor, Validator, and Router into an undocumented monolith without an ADR.
- Bypass validation or routing policy to “simplify” a feature.
- Convert uncertainty into approval as a default architectural behavior.
- Introduce unbounded agent loops, unbounded retries, or missing timeouts on model/tool calls.
- Invent unavailable values at the architecture or contract level (schemas must allow missing/uncertain states).

## When architecture may change

Architecture changes are allowed only when:

1. The task explicitly requires them, or requirements make them necessary.
2. An ADR is added or updated under `docs/decisions/`.
3. Architecture docs (`ARCHITECTURE.md`, `docs/architecture/`) are updated.
4. Affected contracts, tests, and evaluation docs are updated.
5. The PR calls out the architectural delta clearly.

## Contracts

- Stage inputs/outputs should be versionable schemas.
- Router outputs are limited to documented decisions: `AUTO_APPROVE`, `HUMAN_REVIEW`, `AMENDMENT_REQUEST` (unless an ADR expands the set).
- Validation results must support at least `MATCH`, `MISMATCH`, and `UNCERTAIN`.
- Evidence and confidence are first-class fields for extraction outputs—not optional afterthoughts.

## Dependency and layering rules

- Do not introduce new major infrastructure (queues, new databases, new UI frameworks) without an ADR.
- Keep persistence and UI behind clear interfaces so Part 2 triggers/workflows can extend without rewrite.
- Prefer deterministic policy code for routing thresholds where possible; use LLMs only where justified and documented.

## Related documents

- [`agent-development-rules.md`](./agent-development-rules.md)
- [`documentation-rules.md`](./documentation-rules.md)
- Root [`ARCHITECTURE.md`](../../ARCHITECTURE.md) (when present)
- `docs/architecture/`
- `docs/decisions/`
