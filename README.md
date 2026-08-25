# Nova

Operational multi-agent system for **trade and shipping document verification**.

Nova helps control groups replace slow, error-prone manual shipper email loops with a fail-closed pipeline: upload a document, extract structured fields with evidence, validate against customer rules, route a disposition, persist everything, then inspect results in an operations UI or grounded query API.

## Problem

Manual verification of invoices, bills of lading, and related trade documents is:

- Slow (email threads, copy/paste, tribal knowledge)
- Inconsistent across reviewers
- Unsafe to fully automate when fields are missing, ambiguous, or conflicting

Blind auto-approval of uncertain documents creates operational and compliance risk.

## Solution (Part 1)

Nova Part 1 implements a **fail-closed** verification pipeline:

1. Accept a document for a **customer** (and optional **shipment**)
2. Persist content + metadata with **idempotent** ingest
3. **Extract** structured fields with confidence, presence, and evidence
4. **Validate** expected vs found → `MATCH` / `MISMATCH` / `UNCERTAIN`
5. **Route** to exactly one decision → `AUTO_APPROVE` / `HUMAN_REVIEW` / `AMENDMENT_REQUEST`
6. Persist results for ops review and grounded query

Hard rules:

- Never invent unavailable values
- Never silently convert uncertainty into `AUTO_APPROVE`
- On agent/pipeline failure, prefer fail-closed `HUMAN_REVIEW` / `FAILED`

Default LLM path is **MockLLM** (deterministic CI/demo). An optional OpenAI-compatible vision/text adapter can be enabled with credentials; without credentials Nova falls back to MockLLM.

## What Part 1 implements

| Area | Capability |
|------|------------|
| Ingest | Authenticated multipart upload, MIME/size checks, idempotency keys |
| Pipeline | Extractor → Validator → Router orchestration after accept |
| Persistence | PostgreSQL via SQLAlchemy + Alembic migrations |
| Ops reads | Document/shipment/validation/decision APIs + ops summary |
| Query | Allow-listed grounded intents over persisted data (not a chatbot) |
| UI | React Ops dashboard, upload, document/shipment detail, query |
| Deploy | Docker Compose (Postgres + API + UI), health/ready, local CI |

Part 2 (email triggers, multi-doc cross-validation, human approval actions, outbound replies) is **intentionally not implemented**. Extension points: [`docs/architecture/part2-extension-points.md`](./docs/architecture/part2-extension-points.md).

## Main user workflow

```text
Customer
  → Upload document (optional shipment)
  → Persist document + metadata + verification run
  → Processing / extraction
  → Validation (MATCH / MISMATCH / UNCERTAIN)
  → Decision (AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST)
  → Persist result
  → Operations dashboard
  → Grounded query over persisted data
```

### Terminology

| Term | Meaning |
|------|---------|
| **Customer** | Business whose shipment/document data is processed |
| **Shipment** | Shipment belonging to a customer |
| **Document** | Uploaded business document (invoice, BOL, other) |
| **Run** | One processing execution associated with a document/shipment |
| **Validation** | Checks on extracted/document data |
| **Decision** | Router disposition for the run |
| **Query** | Controlled/grounded question over persisted Nova data |

## Architecture

```mermaid
flowchart TB
  User([User / operator])
  UI[Nova Ops UI<br/>React + Vite]
  API[FastAPI /v1]
  Ing[Ingestion service]
  Ops[Ops summary]
  Query[Grounded query]
  Pipe[Pipeline orchestrator]
  Ext[Extractor]
  Val[Validator]
  Rtr[Router]
  Store[(Document object storage)]
  PG[(PostgreSQL)]
  LLM{{LLMPort}}

  User --> UI --> API
  API --> Ing
  API --> Ops
  API --> Query
  Ing -->|bytes| Store
  Ing -->|metadata + run| PG
  Ing --> Pipe
  Pipe --> Ext --> LLM
  Pipe --> Val
  Pipe --> Rtr
  Ext --> PG
  Val --> PG
  Rtr --> PG
  Ops --> PG
  Query --> PG
  API -->|reads| PG
```

### Upload → decision sequence

```mermaid
sequenceDiagram
  participant U as User / Ops UI
  participant API as FastAPI
  participant Ing as Ingestion
  participant S as Object storage
  participant DB as PostgreSQL
  participant P as Pipeline
  participant E as Extractor
  participant V as Validator
  participant R as Router

  U->>API: POST /v1/documents + Idempotency-Key
  API->>Ing: accept multipart
  Ing->>S: store bytes
  Ing->>DB: document, version, run, idempotency
  Ing-->>API: 202 ACCEPTED (document_id, shipment_id, run_id)
  API-->>U: acceptance + IDs
  Ing->>P: run pipeline
  P->>E: extract fields
  E->>DB: append extraction
  P->>V: validate rules
  V->>DB: append validation
  P->>R: route disposition
  R->>DB: append decision + DECIDED
  U->>API: GET /v1/ops/summary or POST /v1/query
  API->>DB: read persisted records
  API-->>U: dashboard / query result
```

Detailed diagram: [`docs/submission/architecture-diagram.md`](./docs/submission/architecture-diagram.md) · [`ARCHITECTURE.md`](./ARCHITECTURE.md)

## Components

| Component | Role | Location |
|-----------|------|----------|
| API | HTTP surface, auth, errors | `src/nova/api/` |
| Ingestion | Accept/store documents, idempotency | `src/nova/application/ingestion.py` |
| Pipeline | Extract → validate → route | `src/nova/application/pipeline.py` |
| Extractor | Structured fields + evidence | `src/nova/extraction/`, `src/nova/agents/` |
| Validator | MATCH / MISMATCH / UNCERTAIN | `src/nova/agents/validator/`, `src/nova/validator/` |
| Router | AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST | `src/nova/router/` |
| Query | Allow-listed grounded intents | `src/nova/query/` |
| Ops | Dashboard aggregates | `src/nova/application/ops.py` |
| Persistence | Models + repositories | `src/nova/persistence/` |
| Frontend | Ops UI | `frontend/` |

## API / backend

Authenticated with `Authorization: Bearer <token>` or `X-API-Key` (`API_AUTH_TOKEN`).

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness |
| `GET` | `/ready` | Readiness (DB + storage) |
| `GET` | `/metrics` | Prometheus text |
| `POST` | `/v1/customers` | Create customer (demo/ops bootstrap) |
| `POST` | `/v1/documents` | Upload (requires `Idempotency-Key`) |
| `GET` | `/v1/documents` | List by customer |
| `GET` | `/v1/documents/{id}` | Detail + extraction summary |
| `GET` | `/v1/documents/{id}/content` | Raw bytes |
| `GET` | `/v1/documents/{id}/validation` | Validation result |
| `GET` | `/v1/documents/{id}/decision` | Routing decision |
| `GET` | `/v1/shipments/{id}` | Shipment + linked documents |
| `GET` | `/v1/ops/summary` | Dashboard aggregates |
| `POST` | `/v1/query` | Grounded query |

Contracts: [`docs/api/`](./docs/api/).

## Database

- **Engine:** PostgreSQL 16 (Compose) / SQLAlchemy 2.x
- **Migrations:** Alembic only (`alembic/versions/`, head `0004_phase7_pipeline`)
- **Entrypoint:** `scripts/entrypoint.sh` waits for DB, then `alembic upgrade head`
- Core tables include customers, shipments, documents, versions, verification runs, extractions, validations, decisions, idempotency records

No production `create_all` schema bootstrap.

## Document processing / extraction

1. MIME sniff + size/extension checks
2. `DocumentProcessorPort` normalizes PDF / plain text / PNG / JPEG
3. Extractor requests assignment fields via `LLMPort`
4. Default **MockLLM** + heuristics for deterministic demos
5. Optional `LLM_PROVIDER=openai` + `LLM_API_KEY` for live vision/text
6. Fields stored append-only with confidence, presence, evidence

## Validation and decision flow

- **Validator** compares expected customer rules vs extracted values → `MATCH` / `MISMATCH` / `UNCERTAIN`
- **Router** applies explicit policy + hard safety constraints → one disposition
- Failures and unsafe paths cannot silently emit `AUTO_APPROVE`
- Results are queryable and visible in the Ops UI

## Dashboard (Ops UI)

React + TypeScript + Vite app in `frontend/`:

| Route | Purpose |
|-------|---------|
| `/` | Ops summary metrics, recent documents/decisions |
| `/upload` | Multipart upload workflow |
| `/documents/:id` | Extraction, validation, decision, content preview |
| `/shipments/:id` | Shipment + linked documents |
| `/query` | Grounded allow-listed query |

All counts and statuses come from live API responses — the UI does not invent aggregates.

## Grounded query system

`POST /v1/query` classifies questions into allow-listed intents and runs parameterized repository reads. It is **not** an open-ended LLM chatbot and does **not** generate SQL.

Supported intents include shipment/document lookup, validation/decision fetch, list-by-decision, list documents for shipment, and summarize run. Out-of-scope questions return `UNSUPPORTED`.

## Local setup (without full Compose UI)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Set non-placeholder API_AUTH_TOKEN and POSTGRES_PASSWORD

cd frontend
cp .env.example .env   # align VITE_API_AUTH_TOKEN with API_AUTH_TOKEN
npm install
```

## Docker setup (recommended)

```bash
cp .env.example .env
# Required: replace API_AUTH_TOKEN and POSTGRES_PASSWORD placeholders
# Startup rejects replace-me / empty tokens

docker compose up --build
```

This:

1. Builds the API and web images
2. Starts PostgreSQL and waits until healthy
3. Runs Alembic migrations via the API entrypoint
4. Starts the API on **http://localhost:8000**
5. Starts the Ops UI on **http://localhost:8080**

Verify:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
# UI: open http://localhost:8080
```

If Alembic complains about unknown revisions after switching branches:

```bash
docker compose down -v
docker compose up --build
```

Optional live LLM:

```bash
# in .env
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

Without credentials, MockLLM remains the default.

## Testing

```bash
# Backend
ruff check src tests
mypy
pytest -q

# Frontend
cd frontend && npm ci && npm test && npm run typecheck && npm run build

# AI evaluation gate (false AUTO_APPROVE must be 0)
PYTHONPATH=src python scripts/run_full_evaluation.py

# Compose recovery smoke (optional)
./scripts/verify-production-readiness.sh
```

PostgreSQL migration tests require a disposable DB:

```bash
export TEST_DATABASE_URL=postgresql+psycopg://nova:nova@localhost:5432/nova_test
export DATABASE_URL="$TEST_DATABASE_URL"
pytest -q
```

## Example end-to-end workflow

1. `docker compose up --build`
2. Open http://localhost:8080 → **Create demo customer**
3. Upload `fixtures/demo/synthetic_invoice_clean.txt` (type `INVOICE`)
4. Note `document_id`, `shipment_id`, `run_id` from the acceptance panel
5. Open the document page → extraction fields, validation, decision
6. Return to dashboard → real totals from `GET /v1/ops/summary`
7. Query: “How many shipments are in human review?”
8. Try an unsupported question (e.g. vessel ETA prediction) → `UNSUPPORTED`
9. Re-upload with the **same** idempotency key → `idempotent_replay: true`

Demo runbook: [`docs/operations/demo-runbook.md`](./docs/operations/demo-runbook.md).

## Project structure

```text
.
├── frontend/                 # React Ops UI
├── src/nova/
│   ├── api/                  # FastAPI routes, DI, errors
│   ├── application/          # Ingestion, pipeline, ops
│   ├── query/                # Grounded query
│   ├── extraction/           # Extractor services + fields
│   ├── agents/               # Agent wrappers
│   ├── validator/            # Validation engine
│   ├── router/               # Decision agent
│   ├── persistence/          # SQLAlchemy models/repos
│   ├── contracts/            # Pydantic wire/domain contracts
│   ├── infrastructure/       # Processors + storage adapters
│   ├── llm/                  # LLMPort adapters (mock / OpenAI-compatible)
│   └── domain/               # Lifecycle policy
├── alembic/                  # Schema migrations
├── tests/                    # Unit, API, query, pipeline, e2e, eval
├── fixtures/demo/            # Synthetic demo documents
├── docs/                     # Requirements, architecture, audits
├── docker-compose.yml
├── Dockerfile
└── scripts/                  # Entrypoint, eval, verify helpers
```

## Configuration / environment variables

See [`.env.example`](./.env.example) and [`docs/deployment/configuration.md`](./docs/deployment/configuration.md).

| Variable | Purpose |
|----------|---------|
| `API_AUTH_TOKEN` | Shared API auth (required; no placeholders) |
| `POSTGRES_*` | Database credentials / DB name |
| `DATABASE_URL` | SQLAlchemy URL (Compose sets this for `api`) |
| `DOCUMENT_STORAGE_PATH` | Blob storage root |
| `MAX_DOCUMENT_SIZE_BYTES` | Upload size limit |
| `ALLOWED_MIME_TYPES` | Allow-listed media types |
| `LLM_PROVIDER` | `mock` (default) or `openai` |
| `LLM_API_KEY` / `LLM_MODEL` | Optional live LLM |
| `CORS_ORIGINS` | Browser origins |
| `API_PORT` / `WEB_PORT` | Host port mapping (defaults 8000 / 8080) |

Never commit real secrets. Compose `web` injects `window.__NOVA_RUNTIME__.apiAuthToken` at container start (not baked into the static build).

## Technology stack

Python 3.12 · FastAPI · Pydantic · SQLAlchemy / Alembic · PostgreSQL 16 · React / Vite / TypeScript · Docker Compose · `LLMPort` (MockLLM default; optional OpenAI-compatible)

## Assignment deliverables

| Deliverable | Location |
|-------------|----------|
| PRD | [`docs/submission/prd.md`](./docs/submission/prd.md) |
| Technical write-up | [`docs/submission/technical-writeup.md`](./docs/submission/technical-writeup.md) |
| Architecture diagram | [`docs/submission/architecture-diagram.md`](./docs/submission/architecture-diagram.md) |
| Traceability map | [`docs/audits/final-gocomet-file-location-map.md`](./docs/audits/final-gocomet-file-location-map.md) |
| Final compliance audit | [`docs/audits/final-gocomet-submission-audit.md`](./docs/audits/final-gocomet-submission-audit.md) |
| Part 1 requirements audit | [`docs/audits/final-part1-audit.md`](./docs/audits/final-part1-audit.md) |

## Current limitations / out of scope

- Live vision cost/latency **not measured** without API keys (absent → MISSING fields, not invented)
- Scanned-PDF OCR adapter deferred (PNG/JPEG vision path covers image MUST)
- Customer rule authoring UI is thin (defaults + request rules)
- Malware/AV scanning not implemented (MIME/size/path only)
- Shared browser API token (no multi-user RBAC)
- Remote production deploy **NOT EXECUTED**
- Part 2 features not implemented (email, multi-doc, approval actions, outbound)

Detail: [`docs/audits/known-limitations.md`](./docs/audits/known-limitations.md).

## License

License not yet chosen.
