# Phase 3 audit — Application foundation + document ingestion

| Field | Value |
|-------|-------|
| Date | 2026-08-25 |
| Scope | Application foundation, PostgreSQL persistence for ingestion entities, document upload/storage/processing, Docker Compose, CI |
| Auditor | Principal Engineer (Phase 3 integration) |
| Branch | `feature/phase-3-integration` |
| Verdict | **PASS** (no unresolved CRITICAL or HIGH findings) |

## 1. Scope

Phase 3 delivers:

- FastAPI application foundation (config, lifecycle, errors, auth)
- PostgreSQL + Alembic for ingestion entities
- Document ingestion API with idempotency
- Local document storage + `DocumentProcessorPort` (PDF/text)
- Structured logging with `request_id` / `trace_id`
- Docker Compose + CI

Explicitly **out of scope** (deferred):

- Real Extractor / Validator / Router agents and LLM calls
- OCR for scanned PDFs
- Malware scanning
- Frontend / NL query / validation & decision retrieval handlers

Integration sources (semantic merge, not blind ours/theirs):

| Branch | Role taken |
|--------|------------|
| `feature/phase-3-backend-foundation` | API/ingestion/DB/idempotency patterns and tests |
| `feature/phase-3-document-processing` | Canonical `nova.documents` processor package, fixtures, docs |
| `feature/phase-3-ops-quality` | Observability metrics, Docker/entrypoint wait, CI structure |
| Phase 2 tip `feature/phase-2-integration` | Frozen contracts + integrated architecture docs (base) |

All three Phase 3 feature branches were originally cut from `feature/phase-2-architecture` (missing later Phase 2 integration commits). Integration rebased the strongest pieces onto `feature/phase-2-integration`.

## 2. Implemented features

| Feature | Status |
|---------|--------|
| FastAPI app + lifespan | Done |
| Env configuration (`Settings`) | Done |
| `GET /health` | Done |
| `GET /ready` (DB schema + storage) | Done |
| `GET /metrics` (Prometheus) | Done |
| `POST /v1/documents` → **202** | Done |
| Required `Idempotency-Key` + replay/409 | Done |
| `GET /v1/documents/{id}` | Done |
| `GET /v1/shipments/{id}` | Done |
| API key auth (Bearer / X-API-Key) | Done |
| Alembic `0001_phase3_foundation` | Done |
| Local filesystem storage (path-safe) | Done |
| Digital PDF + text processors | Done |
| Structured JSON logs + correlation IDs | Done |
| Docker Compose (API + PostgreSQL) | Done |
| CI (docs, secrets, ruff, mypy, pytest, migrations, docker build) | Done |

## 3. Architecture verification

Verified layering:

```text
API (FastAPI routes/deps)
  → application/ingestion
  → domain errors + lifecycle
  → persistence (SQLAlchemy)
  → PostgreSQL

bytes → DocumentStoragePort / LocalFilesystemStorage
     → DocumentProcessingService / DocumentProcessorPort
     → DocumentContent (nova.contracts.common)
```

- Routes do not import SQLAlchemy engines or pypdf directly.
- Ingestion uses `DocumentProcessingService` from `nova.documents`.
- Phase 2 Pydantic contracts under `src/nova/contracts/` are unchanged (`extra="forbid"` preserved).

## 4. Database verification

Migration: `alembic/versions/0001_phase3_foundation.py`

Tables present: `customers`, `shipments`, `documents`, `document_versions`, `verification_runs`, `idempotency_records` (+ `alembic_version`).

Verified:

- Foreign keys and CHECK constraints per Phase 2 schema design (ingestion subset)
- Unique indexes for external keys, shipment refs, version numbers, idempotency keys
- Document versions treated as immutable content rows in application code
- Ingest persists document + version + run + idempotency record transactionally; orphan blob cleanup on DB failure
- Clean DB: `alembic upgrade head` then second `upgrade head` (no-op) — **PASS**
- Revision reported: `0001_phase3_foundation (head)`

## 5. API verification

| Check | Result |
|-------|--------|
| `GET /health` → 200 `{"status":"ok"}` | PASS (pytest + Compose smoke) |
| `GET /ready` → 200 with checks | PASS |
| `POST /v1/documents` → 202 ACCEPTED | PASS |
| Idempotent replay → 202 `idempotent_replay: true` | PASS |
| Fingerprint mismatch → 409 | PASS (pytest) |
| Missing auth → 401 | PASS |
| Missing Idempotency-Key → 400 | PASS (pytest) |
| Unsupported MIME → 422 | PASS |
| Unsafe filename / traversal → 422 | PASS |
| Ready when DB down → 503 without secrets | PASS (pytest) |
| Stack traces / tokens absent from bodies | PASS |

Compose smoke (project `nova-p3-audit`, API `:18000`): health, ready, ingest 202, replay, GET document/shipment, unsafe filename, bad MIME — all observed.

## 6. Document processing verification

| Case | Result |
|------|--------|
| Supported text/plain | PASS |
| Supported digital PDF (pypdf) | PASS (`tests/documents/`) |
| Unsupported MIME | Rejected 422 |
| Corrupt / malformed PDF | Covered in document tests |
| Oversized payload | Covered (limits + large-file tests) |
| Unsafe filenames / path traversal | Rejected |
| Contents never logged | Logging redaction + no body fields in request logs |

## 7. Security verification

| Control | Result |
|---------|--------|
| Path traversal in storage/filenames | PASS |
| Secret pattern CI script | PASS |
| Auth required on ingest/retrieval | PASS |
| Placeholder `API_AUTH_TOKEN` rejected outside test | PASS |
| No stack traces in HTTP errors | PASS |
| DB credentials not in error bodies | PASS |
| `.env` gitignored; `.env.example` placeholders only | PASS |
| Compose `DATABASE_URL` forced to `@db` (no host URL leak) | PASS (fixed during audit) |

## 8. Observability verification

| Requirement | Result |
|-------------|--------|
| `request_id` + `trace_id` on responses/headers | PASS |
| Structured JSON logs (`timestamp`, `level`, `service`, `environment`, `event`, `duration_ms`, `status`) | PASS |
| Document bytes not logged | PASS |
| `/metrics` Prometheus counters/latency | PASS |

## 9. Testing results (exact)

Commands run in `/home/utkarsh/Documents/Github/nova-phase3-integration`:

```text
ruff check src tests
→ All checks passed!  (exit 0)

mypy
→ Success: no issues found in 47 source files  (exit 0)

TEST_DATABASE_URL=postgresql+psycopg://nova:nova@127.0.0.1:5432/nova_phase3_audit \
APP_ENV=test pytest -q
→ 55 passed, 1 warning (Starlette TestClient deprecation)  (exit 0)

alembic upgrade head  # clean DB nova_phase3_clean
→ Running upgrade  -> 0001_phase3_foundation  (exit 0)
alembic upgrade head  # repeat
→ no-op (exit 0)
alembic current
→ 0001_phase3_foundation (head)

./scripts/check-docs-structure.sh → PASSED
./scripts/check-secret-patterns.sh → PASSED
```

## 10. Benchmark results

```text
python scripts/benchmark_document_processing.py
processor_version=1.0.0
name,bytes,status,duration_ms,rss_kb
text_invoice,122,SUCCEEDED,0.432,37576
pdf_1page,613,SUCCEEDED,1.575,37576
pdf_3page,1232,SUCCEEDED,2.496,37704
pdf_5page,1851,SUCCEEDED,3.885,37832
```

Informational only; within soft ceilings in `docs/documents/benchmarks.md`.

## 11. Docker verification

```text
docker compose build → Image built (exit 0)
docker compose -p nova-p3-audit up -d → API healthy after migration
curl /health → {"status":"ok"}
curl /ready → database/object_storage ok
POST /v1/documents → HTTP 202
```

Entrypoint waits for DB, runs `alembic upgrade head`, then uvicorn (non-root image).

## 12. CI verification

Local CI-equivalent steps above: **PASS**.

GitHub Actions: verified by pushing `feature/phase-3-integration` and inspecting workflow runs (see section appendix / verification report). **Do not treat local green as remote CI green until Actions report success.**

Workflow (`.github/workflows/ci.yml`) includes: docs/secrets, ruff, mypy, pytest with Postgres service, migration validation for six tables, `docker build`.

## 13. Requirement traceability

Updated `docs/requirements/traceability.md` § Phase 3 implementation evidence.

Implemented (with Implementation → Test → Evidence): REQ-EXT-001, REQ-EXT-006 (edge isolation), REQ-DATA-001/002/003 (ingestion subset), REQ-QUERY-001 (partial GET), REQ-OBS-001/002/004 (partial), REQ-TEST-001/003–004, REQ-DEPLOY-003–004, REQ-DOC-001–003, REQ-SEC-001–004.

**Not claimed:** REQ-EXT-002–005, REQ-AI-* runtime agents, validation/router/query NL, UI.

## 14. Known limitations

- No OCR for scanned/image-only PDFs
- No malware scanning
- Synchronous intake normalization before returning 202 (run remains `queued`; no Extractor)
- Part 1 shared API token only (no RBAC)
- SQLite used in some unit/API fixtures; production path is PostgreSQL (integration tests cover PG)
- Starlette `TestClient` deprecation warning (httpx2) — non-blocking

## 15. Technical debt

| ID | Severity | Item |
|----|----------|------|
| TD-01 | LOW | Unify Settings env aliases (`APP_ENV` vs legacy `ENVIRONMENT`) fully in docs |
| TD-02 | LOW | Replace Starlette TestClient when httpx2 lands |
| TD-03 | MEDIUM | Optional async worker for post-accept processing (Phase 4 Extractor) |
| TD-04 | LOW | Expand malware/content threat model for production |

## 16. Part 2 compatibility

- 1:N documents per shipment preserved (no unique-on-shipment constraint)
- `IngestionPort` / email channel reserved; HTTP `source_path` not enabled in Phase 3
- Processor port remains the attachment processing boundary for future email adapters

## 17. Phase 4 readiness

Ready to implement Extractor against frozen `ExtractionResult` / `DocumentContent` contracts:

- Stable `document_id`, `document_version_id`, `run_id`, stored bytes, processor output
- Verification runs created in `queued` state
- Observability IDs and error model in place

**Do not** start Validator/Router until Extractor produces contract-valid fields with confidence/evidence.

## Findings

| ID | Severity | Finding | Resolution |
|----|----------|---------|------------|
| F-01 | HIGH (resolved) | Compose interpolated host `DATABASE_URL` into API container (`127.0.0.1`) | Fixed: Compose builds URL with `@db` from POSTGRES_* only |
| F-02 | MEDIUM (resolved) | API tests could pick env `API_AUTH_TOKEN` over fixture token | Fixed: fixture sets explicit `api_auth_token` |
| F-03 | LOW | Parallel Phase 3 branches based on incomplete Phase 2 tip | Integrated onto `feature/phase-2-integration` |
| F-04 | LOW | Starlette TestClient deprecation warning | Accepted debt TD-02 |

No open CRITICAL or HIGH issues remain.

## Acceptance checklist

| Criterion | Status |
|-----------|--------|
| FastAPI application runs | PASS |
| PostgreSQL runs | PASS |
| Migrations work (clean + repeat) | PASS |
| Health works | PASS |
| Readiness works | PASS |
| Document ingestion works | PASS |
| Idempotency works | PASS |
| Document storage works | PASS |
| Document processing works | PASS |
| Error model works | PASS |
| Structured logging works | PASS |
| Trace/request IDs work | PASS |
| Docker Compose works | PASS |
| Ruff / MyPy / tests / failure / security | PASS (local) |
| Documentation + traceability updated | PASS |
| Phase 3 audit PASS | **PASS** |
| GitHub Actions CI | Pending remote run after push |

## Appendix — key paths

- `src/nova/api/`, `src/nova/application/ingestion.py`
- `src/nova/documents/`, `src/nova/persistence/`, `src/nova/observability/`
- `alembic/versions/0001_phase3_foundation.py`
- `docs/features/document-ingestion.md`, `docs/documents/`, `docs/architecture/document-processing.md`
