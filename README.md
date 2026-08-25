# Nova

Operational multi-agent AI system for **trade/shipping document verification**.

Nova accepts documents such as invoices and Bills of Lading, extracts key fields with confidence and evidence, checks them against customer-specific rules, and routes each case to **AUTO_APPROVE**, **HUMAN_REVIEW**, or **AMENDMENT_REQUEST**. Results are persisted and queryable through a minimal B2B operations UI.

This is an operational verification system — not a generic chatbot and not a hackathon prototype.

## Status

**Phase 11 — Deployment, security hardening, observability, and production readiness** (on top of Phases 3–10)

| Area | Status |
|------|--------|
| Phase 1 foundation | Complete |
| Technology ADRs (0002–0009) | Accepted |
| End-to-end pipeline | Implemented (Extractor → Validator → Router) |
| Grounded Query API | Implemented (`POST /v1/query`) |
| Operations UI (React/TS/Vite) | Implemented (`frontend/`) |
| Compose deploy (api + db + web) | Hardened (non-root, runtime web secrets) |
| Remote production deploy | **NOT EXECUTED** |
| Live vendor LLM | Optional; MockLLM default |

Production readiness audit (checklist): [`docs/audits/phase-11-production-readiness.md`](./docs/audits/phase-11-production-readiness.md).

Deploy runbook: [`docs/deployment/production.md`](./docs/deployment/production.md).

## Quick links

| Audience | Start here |
|----------|------------|
| AI coding agents | [AGENTS.md](./AGENTS.md) |
| Contributors | [CONTRIBUTING.md](./CONTRIBUTING.md) |
| UI demo | [docs/operations/ui-demo.md](./docs/operations/ui-demo.md) |
| Recovery | [docs/operations/recovery.md](./docs/operations/recovery.md) |
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
cd frontend && npm test && npm run typecheck && npm run build
./scripts/verify-production-readiness.sh
```

## Run locally

Set a non-placeholder `API_AUTH_TOKEN` and database password in `.env`, then:

```bash
docker compose up --build
curl http://localhost:8000/health
# UI: http://localhost:8080
```

Authenticated endpoints accept `Authorization: Bearer <token>` or `X-API-Key`.
`POST /v1/documents` requires multipart form data and an `Idempotency-Key`, and
returns `202 Accepted`. The pipeline runs Extractor → Validator → Router (MockLLM by default).

Frontend env template: `frontend/.env.example`. Demo walkthrough: [docs/operations/ui-demo.md](./docs/operations/ui-demo.md).

## License

License not yet chosen.
