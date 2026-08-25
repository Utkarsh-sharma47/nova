# Nova

Operational multi-agent AI system for **trade/shipping document verification**.

Nova accepts documents such as invoices and Bills of Lading, extracts key fields with confidence and evidence, checks them against customer-specific rules, and routes each case to **AUTO_APPROVE**, **HUMAN_REVIEW**, or **AMENDMENT_REQUEST**. Results are persisted in PostgreSQL and queryable through a grounded query API and a minimal B2B operations UI.

This is an operational verification system — not a generic chatbot.

## Problem

Manual shipper ↔ validation-team email loops are slow, expensive, and error-prone. Blind automation is unsafe when documents are messy, incomplete, or ambiguous.

## Solution (Part 1)

A fail-closed pipeline:

```text
Upload → process → Extractor → Validator → Router → PostgreSQL → Query / UI
```

Uncertainty and failures prefer **HUMAN_REVIEW** (or safe halt) over silent approval. Critical evaluation gate: **false AUTO_APPROVE = 0**.

## Part 1 scope

| Included | Not included (Part 2) |
|----------|------------------------|
| Single-document upload (invoice / BoL) | Email ingestion |
| Extraction + confidence + evidence | Multi-attachment workflows |
| Customer rules validation | Cross-document verification |
| AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST | Human approval action UX |
| Persistence + grounded NL query | Draft replies / outbound send |
| Minimal ops UI + Docker Compose demo | Extra ingestion channels |

## Architecture

```text
┌─────────────┐     ┌──────────────────────────────────────────────┐
│ React UI    │────▶│ FastAPI (/v1/documents, /validation,         │
│ (ops)       │◀────│  /decision, /query, /ops, /health|/ready)    │
└─────────────┘     └───────────────┬──────────────────────────────┘
                                    │
                    ┌───────────────▼──────────────────────────────┐
                    │ PipelineOrchestrator                         │
                    │  Extractor → Validator → Router              │
                    │  (LLMPort / MockLLM default)                 │
                    └───────┬───────────────┬──────────────────────┘
                            │               │
              ┌─────────────▼──┐   ┌────────▼────────┐
              │ Document store │   │ PostgreSQL      │
              │ (local FS)     │   │ (system of      │
              └────────────────┘   │  record +       │
                                   │  append-only AI │
                                   │  history)       │
                                   └────────┬────────┘
                                            │
                                   ┌────────▼────────┐
                                   │ Grounded Query  │
                                   │ (no LLM SQL)    │
                                   └─────────────────┘
                         Observability: structured logs,
                         request/trace/run/agent IDs, /metrics
```

Detail: [ARCHITECTURE.md](./ARCHITECTURE.md) · [docs/architecture/](./docs/architecture/).

## Technology stack

| Layer | Choice |
|-------|--------|
| Backend | Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 |
| LLM | Provider-agnostic `LLMPort` (MockLLM default) |
| Frontend | React + TypeScript + Vite |
| Deploy | Docker Compose (non-root API + nginx-unprivileged web) |

ADRs: [docs/decisions/](./docs/decisions/).

## AI agents

| Agent | Role |
|-------|------|
| Extractor | Required fields + confidence + evidence; anti-fabrication |
| Validator | Deterministic rules first; MATCH / MISMATCH / UNCERTAIN |
| Router | Disposition under explicit policy; fail-closed |

## Database & API

- PostgreSQL is the system of record; schema via **Alembic only** (no production `create_all`).
- Core endpoints: document ingest/list/get, validation/decision reads (document + shipment aliases), grounded `POST /v1/query`, ops summary, `/health` `/ready` `/metrics`.
- `POST /v1/documents` requires auth + `Idempotency-Key` → `202 Accepted`.

## Frontend

Minimal logistics-style ops UI: dashboard, upload, document/shipment detail (extraction/validation/decision), grounded query. Data comes from the API — no fake business mocks in runtime.

## Evaluation & safety

```bash
PYTHONPATH=src python scripts/run_full_evaluation.py
```

Reports: `docs/evaluation/reports/`. Decision regression must keep **false AUTO_APPROVE = 0**.

## Security & observability

- Secrets via `.env` (gitignored); pattern scan in CI
- Upload type/size/path controls; query rejects SQL/schema/prompt injection
- Structured JSON logs with correlation IDs; no document bodies/secrets in logs by policy

## Local setup

```bash
cp .env.example .env   # set API_AUTH_TOKEN + DB password
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
# optional non-Docker API requires local Postgres + alembic upgrade head
```

## Docker setup

```bash
docker compose up --build
curl http://localhost:8000/health
# UI http://localhost:8080
```

## Testing

```bash
ruff check src tests && mypy && pytest -q
cd frontend && npm ci && npm test && npm run typecheck && npm run build
./scripts/check-docs-structure.sh && ./scripts/check-secret-patterns.sh
```

## Demo

Follow [docs/operations/demo-runbook.md](./docs/operations/demo-runbook.md) (synthetic fixtures only).

## Deployment

Local/Compose: [docs/deployment/](./docs/deployment/). Remote production host deploy: **NOT EXECUTED** (procedure documented).

## Limitations

See [docs/audits/known-limitations.md](./docs/audits/known-limitations.md). Final audit: [docs/audits/final-part1-audit.md](./docs/audits/final-part1-audit.md).

## Part 2 roadmap

Email/file triggers, multi-doc + cross-doc validation, human approval actions, draft replies, outbound send — **PLANNED, NOT IMPLEMENTED IN PART 1**. Extension points: [docs/architecture/part2-extension-points.md](./docs/architecture/part2-extension-points.md).

## Status

**Phase 12 — Final Part 1 release audit** (`PASS WITH LIMITATIONS`).

| Audience | Start here |
|----------|------------|
| Reviewers / demo | [docs/operations/demo-runbook.md](./docs/operations/demo-runbook.md) |
| AI coding agents | [AGENTS.md](./AGENTS.md) |
| Requirements | [docs/requirements/inventory.md](./docs/requirements/inventory.md) |
| Architecture | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| Roadmap | [ROADMAP.md](./ROADMAP.md) |

## License

License not yet chosen.
