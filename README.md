# Nova

Operational multi-agent AI system for **trade/shipping document verification**.

Nova accepts documents such as invoices and Bills of Lading, extracts key fields with confidence and evidence, checks them against customer-specific rules, and routes each case to **AUTO_APPROVE**, **HUMAN_REVIEW**, or **AMENDMENT_REQUEST**. Results are persisted and queryable through a minimal B2B operations UI.

This is an operational verification system — not a generic chatbot and not a hackathon prototype.

## Status

**Phase 1 — Engineering foundation**

| Area | Status |
|------|--------|
| Requirements inventory (`REQ-*`) | Documented |
| Product / problem / solution | Documented |
| Part 1 scope & Part 2 extension points | Documented |
| Architecture principles & standards | Documented |
| Documentation system | Established |
| Git workflow | Documented |
| CI foundation | Docs structure + secret patterns |
| AI agent governance | Established (`AGENTS.md` + `docs/ai-development/`) |
| Application implementation | **Not started** |

## Quick links

| Audience | Start here |
|----------|------------|
| AI coding agents | [AGENTS.md](./AGENTS.md) |
| Contributors | [CONTRIBUTING.md](./CONTRIBUTING.md) |
| Requirements | [docs/requirements/inventory.md](./docs/requirements/inventory.md) |
| Part 1 scope | [docs/features/part1-scope.md](./docs/features/part1-scope.md) |
| Architecture | [ARCHITECTURE.md](./ARCHITECTURE.md) · [docs/architecture/](./docs/architecture/) |
| Roadmap | [ROADMAP.md](./ROADMAP.md) |
| Git workflow | [docs/operations/git-workflow.md](./docs/operations/git-workflow.md) |
| Full docs tree | [docs/README.md](./docs/README.md) |

## Conceptual pipeline

```text
Document → ingestion → extraction → confidence/evidence
        → validation → routing → persistence → query → UI
```

Details: [docs/product/solution-definition.md](./docs/product/solution-definition.md)

## Part 1 vs Part 2

- **Part 1:** single-document path, customer rules, MATCH/MISMATCH/UNCERTAIN, router decisions, persistence, NL query, minimal UI, samples, evaluation, observability, docs.
- **Part 2 (later):** email/file triggers, multiple attachments, cross-document validation, draft replies, human approval, outbound sending.

Extension points only in Part 1: [docs/architecture/part2-extension-points.md](./docs/architecture/part2-extension-points.md)

## Local checks (Phase 1)

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
```

## License

License not yet chosen.
