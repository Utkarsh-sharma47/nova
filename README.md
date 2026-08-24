# Nova

Operational multi-agent AI system for **trade/shipping document verification**.

Nova accepts documents such as invoices and Bills of Lading, extracts key fields with confidence and evidence, checks them against customer-specific rules, and routes each case to **AUTO_APPROVE**, **HUMAN_REVIEW**, or **AMENDMENT_REQUEST**. Results are persisted and queryable through a minimal B2B operations UI.

This is an operational verification system — not a generic chatbot and not a hackathon prototype.

## Status

**Phase 3 — Application foundation and document ingestion**

| Area | Status |
|------|--------|
| Phase 1 foundation | Complete |
| Technology ADRs (0002–0009) | Accepted |
| System / AI / DB / API architecture docs | Documented |
| Pydantic domain contracts | In `src/nova/contracts/` |
| FastAPI ingestion and retrieval | Implemented |
| PostgreSQL / Alembic foundation | Implemented |
| Local document processing/storage | PDF and UTF-8 text |
| Extractor / Validator / Router agents | **Not implemented** |
| UI / live LLM | **Not implemented** |

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

## Run locally

Set a non-placeholder `API_AUTH_TOKEN` and database password in `.env`, then:

```bash
docker compose up --build
curl http://localhost:8000/health
```

Authenticated endpoints accept `Authorization: Bearer <token>` or `X-API-Key`.
`POST /v1/documents` requires multipart form data and an `Idempotency-Key`, and
returns `202 Accepted`. Phase 3 stores and normalizes content, creates a queued
verification run, and does not execute extraction or any LLM agent.

## License

License not yet chosen.
