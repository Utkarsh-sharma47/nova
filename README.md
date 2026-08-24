# Nova

Operational multi-agent AI system for **trade/shipping document verification**.

Nova accepts documents such as invoices and Bills of Lading, extracts key fields with confidence and evidence, checks them against customer-specific rules, and routes each case to **AUTO_APPROVE**, **HUMAN_REVIEW**, or **AMENDMENT_REQUEST**. Results are persisted and queryable through a minimal B2B operations UI.

This is an operational verification system — not a generic chatbot and not a hackathon prototype.

## Status

**Phase 2 — Technology architecture & domain contracts**

| Area | Status |
|------|--------|
| Phase 1 foundation | Complete |
| Technology ADRs (0002–0009) | Accepted |
| System / AI / DB / API architecture docs | Documented |
| Pydantic domain contracts | In `src/nova/contracts/` |
| Agent business logic | **Not started** (Phase 3–4) |
| ORM / UI / live LLM | **Not started** |

## Quick links

| Audience | Start here |
|----------|------------|
| AI coding agents | [AGENTS.md](./AGENTS.md) |
| Contributors | [CONTRIBUTING.md](./CONTRIBUTING.md) |
| Requirements | [docs/requirements/inventory.md](./docs/requirements/inventory.md) |
| Architecture | [ARCHITECTURE.md](./ARCHITECTURE.md) · [docs/architecture/](./docs/architecture/) |
| Stack ADRs | [docs/decisions/](./docs/decisions/) |
| Contracts | [docs/architecture/contracts.md](./docs/architecture/contracts.md) |
| Roadmap | [ROADMAP.md](./ROADMAP.md) |
| Full docs tree | [docs/README.md](./docs/README.md) |

## Conceptual pipeline

```text
Document → ingestion → extraction → confidence/evidence
        → validation → routing → persistence → query → UI
```

## Local checks

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
pip install -e ".[dev]"
ruff check src tests
mypy
pytest -q
```

## License

License not yet chosen.
