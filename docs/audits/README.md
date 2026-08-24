# Audits

Periodic audits of documentation quality, agent compliance, architecture drift, and delivery readiness.

## Purpose

Audits create an honest snapshot of gaps and risks. They must not invent passing results or unimplemented capabilities.

## Creating an audit

1. Copy [AUDIT_TEMPLATE.md](AUDIT_TEMPLATE.md).
2. Name files `YYYY-MM-DD-short-title.md`.
3. Link the audit from this README.
4. File follow-up work as issues or roadmap items.

## Audit index

| Date | Title | Status |
|------|-------|--------|
| _(none yet)_ | | |

## Phase 1 baseline inputs (for the first audit)

- Requirements inventory completeness (`docs/requirements/inventory.md`)
- CI honesty (docs/secrets checks only; no fake app tests)
- Secrets hygiene (`.gitignore`, secret pattern script)
- AI governance presence (`AGENTS.md`, `docs/ai-development/`)

## Related

- [AUDIT_TEMPLATE.md](AUDIT_TEMPLATE.md)
- [AI development](../ai-development/)
- [Roadmap](../roadmap/)
