# Nova

Operational multi-agent AI system for **trade/shipping document verification**.

Nova accepts documents such as invoices and Bills of Lading, extracts key fields with confidence and evidence, checks them against customer-specific rules, and routes each case to **AUTO_APPROVE**, **HUMAN_REVIEW**, or **AMENDMENT_REQUEST**. Results are persisted and queryable through a minimal B2B operations UI.

This is an operational verification system — not a generic chatbot and not a hackathon prototype.

## Status

**Phase 3 — Backend foundation (ingestion)**

| Area | Status |
|------|--------|
| Phase 1–2 foundation + contracts | Complete |
| Config / domain lifecycle / observability | Implemented |
| PostgreSQL models + Alembic migration | Implemented |
| Local document storage | Implemented |
| `POST /v1/documents` + `/health` + `/ready` | Implemented |
| Extractor / Validator / Router agents | **Not started** |
| LLM provider calls | **Not in Phase 3** |

## Quick links

| Audience | Start here |
|----------|------------|
| AI coding agents | [AGENTS.md](./AGENTS.md) |
| Contributors | [CONTRIBUTING.md](./CONTRIBUTING.md) |
| Local development | [DEVELOPMENT.md](./DEVELOPMENT.md) |
| API surface | [docs/api/](./docs/api/) |
| Database | [docs/database/](./docs/database/) |
| Deployment | [docs/deployment/](./docs/deployment/) |
| Architecture | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| Roadmap | [ROADMAP.md](./ROADMAP.md) |

## Conceptual pipeline

```text
Document → ingestion → extraction → confidence/evidence
        → validation → routing → persistence → query → UI
```

Phase 3 implements **ingestion only**: multipart upload, idempotent accept (`202`), queued verification run row. No agent/LLM execution yet.

## Local quickstart

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
docker compose up -d db
# create test DB if needed: docker compose exec db createdb -U nova nova_test
alembic upgrade head
uvicorn nova.api.main:create_app --factory --reload
```

Or full stack: `API_AUTH_TOKEN=… docker compose up --build`

## Local checks

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
ruff check src tests
mypy
pytest -q
```

Integration tests expect PostgreSQL at `TEST_DATABASE_URL` (default `postgresql+asyncpg://nova:nova@localhost:5432/nova_test`).

## License

License not yet chosen.
