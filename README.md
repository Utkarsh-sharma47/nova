# Nova

Operational multi-agent AI system for **trade/shipping document verification**.

Nova accepts documents such as invoices and Bills of Lading, extracts key fields with confidence and evidence, checks them against customer-specific rules, and routes each case to **AUTO_APPROVE**, **HUMAN_REVIEW**, or **AMENDMENT_REQUEST**. Results are persisted and queryable through a minimal B2B operations UI.

This is an operational verification system — not a generic chatbot and not a hackathon prototype.

## Status

**Phase 3 — Operational foundation** (deploy, observability, CI quality)

| Area | Status |
|------|--------|
| Phase 1–2 foundation + contracts | Complete |
| Docker Compose (API + Postgres) | Implemented |
| Alembic bootstrap migration | Implemented |
| Structured logs + request/trace IDs | Implemented |
| Prometheus baseline metrics | Implemented |
| `/health`, `/ready`, `/metrics` | Implemented |
| Agent business logic | **Not started** (product Phase 3–4) |
| Full domain ORM / UI | **Not started** |

## Quick start

```bash
git clone https://github.com/Utkarsh-sharma47/nova.git
cd nova
cp .env.example .env
docker compose up --build
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/ready
```

See [DEVELOPMENT.md](./DEVELOPMENT.md) and [docs/deployment/local.md](./docs/deployment/local.md).

## Quick links

| Audience | Start here |
|----------|------------|
| AI coding agents | [AGENTS.md](./AGENTS.md) |
| Contributors | [CONTRIBUTING.md](./CONTRIBUTING.md) |
| Requirements | [docs/requirements/inventory.md](./docs/requirements/inventory.md) |
| Architecture | [ARCHITECTURE.md](./ARCHITECTURE.md) · [docs/architecture/](./docs/architecture/) |
| Deployment | [docs/deployment/](./docs/deployment/) |
| Observability | [docs/observability/](./docs/observability/) |
| Roadmap | [ROADMAP.md](./ROADMAP.md) |

## Conceptual pipeline

```text
Document → ingestion → extraction → confidence/evidence
        → validation → routing → persistence → query → UI
```

## Local checks

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
./scripts/check-dockerfile.sh
pip install -e ".[dev]"
ruff check src tests
mypy
pytest -q -m "not ops"
```

## License

License not yet chosen.
