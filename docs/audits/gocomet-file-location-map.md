# GoComet Nova — File Location Map

Third-party verification map: **requirement → code → tests → docs → how to prove it**.

Companion audit: [`gocomet-final-rubric-audit.md`](./gocomet-final-rubric-audit.md).

---

## How to use this map

1. Prefer **code + tests** over README claims.
2. For each row, run the listed command or open the listed UI path.
3. Classification of demonstrability is in the audit (VISIBLE / API / TEST / DOC-ONLY / MISSING).

---

## Deliverable 1 — PRD / product narrative

| Requirement | Actual implementation | Path | Symbol / artifact | Test | Documentation | Third-party verify |
|-------------|----------------------|------|-------------------|------|---------------|-------------------|
| What is Nova / problem | Product prose only (not GoComet PRD) | `docs/product/problem-definition.md`, `docs/product/solution-definition.md`, `README.md` | — | — | same | Read docs; confirm **no** FDE / System of Outcomes / JTBD |
| Personas | Validation analyst (not CG/SU) | `docs/product/personas-and-users.md` | — | — | same | Grep for `CG` / `JTBD` → expect empty |
| Agent rationale | Thin AI architecture note | `docs/architecture/ai-architecture.md`, `docs/decisions/0010-ai-agent-contracts-and-trust-model.md` | — | — | `docs/agents/` | Confirm missing “why not 1 / why not 5” |
| Trust / evals narrative | Trust model + eval docs | `docs/agents/trust-model.md`, `docs/evaluation/` | — | eval scripts | same | Read; note not packaged as PRD §6–7 |
| Roadmap | Phase 1–12 complete + Part 2 | `ROADMAP.md`, `docs/roadmap/roadmap.md` | — | — | same | Confirm **no** two-week pilot Go/No-Go |

---

## Deliverable 2A — Extractor

| Requirement | Actual implementation | Path | Class / function | Test | Documentation | Third-party verify |
|-------------|----------------------|------|------------------|------|---------------|-------------------|
| Extractor service | Implemented | `src/nova/extraction/service.py` | `ExtractorService.extract` | `tests/extraction/` | `docs/agents/extractor.md`, `docs/features/extractor-agent.md` | Unit/integration tests; upload demo invoice |
| Field catalog (Nova Part 1) | Invoice + BOL tuples | `src/nova/extraction/fields.py` | `INVOICE_FIELDS`, `BILL_OF_LADING_FIELDS` | `tests/extraction/test_extractor_service.py` | agent docs | **Open file** — confirm `hs_code` / `incoterms` / `description_of_goods` / `gross_weight` absent |
| Heuristic mock extract | Line-label parser | `src/nova/extraction/heuristic.py` | `heuristic_extractor_response` | extraction tests | fixtures README | Upload `fixtures/demo/synthetic_invoice_clean.txt` |
| Prompts / parsing | Versioned prompt + JSON normalize | `src/nova/extraction/prompts.py`, `parsing.py` | `build_extraction_prompt`, `normalize_field_dicts` | extraction tests | trust-model | Inspect prompt; assert schema validation |
| LLM port | Text-only protocol | `src/nova/llm/port.py` | `LLMPort.complete` | used across tests | ADR-0005 | Confirm no image/vision content type |
| Mock LLM | Only concrete adapter | `src/nova/llm/mock.py` | `MockLLM` | widespread | `known-limitations.md` | `build_default_llm` in `application/extraction.py` falls back to mock |
| LLM factory | Mock default | `src/nova/application/extraction.py` | `build_default_llm` | phase/pipeline tests | features/extractor | Set non-mock provider → still mock (warning log) |
| PDF accept | Digital text PDF | `src/nova/documents/adapters/digital_pdf.py` | `DigitalPdfAdapter` | `tests/documents/` | `docs/documents/supported-types.md` | Upload `.pdf` with embedded text |
| Image accept | **Rejected** | `src/nova/documents/limits.py`, `frontend/src/pages/UploadPage.tsx` | `SUPPORTED_MEDIA_TYPES`, `ACCEPTED_TYPES` | `tests/api/test_documents_api.py` (png → UNSUPPORTED) | supported-types.md | Upload `.png` → expect rejection |
| Contracts | Pydantic fields + evidence | `src/nova/contracts/extraction.py` | `ExtractedField`, `ExtractionResult` | `tests/contracts/test_schemas.py` | `docs/agents/contracts.md` | Instantiate invalid KNOWN without evidence → ValidationError |
| Application wiring | Persist extraction | `src/nova/application/extraction.py` | `ExtractionApplicationService` | pipeline e2e | `docs/architecture/end-to-end-pipeline.md` | GET document after upload |

**Run (extractor path):**

```bash
docker compose up --build
# UI: create customer → upload fixtures/demo/synthetic_invoice_clean.txt as INVOICE
# Expect fields like invoice_number, seller_name, … — NOT hs_code / gross_weight
```

---

## Deliverable 2B — Validator

| Requirement | Actual implementation | Path | Class / function | Test | Documentation | Third-party verify |
|-------------|----------------------|------|------------------|------|---------------|-------------------|
| Validator agent | Deterministic + optional LLM judgment | `src/nova/agents/validator/agent.py` | `ValidatorAgent.validate` | `tests/` validator + evaluation | `docs/agents/validator.md` | Eval report unsafe_match=0 |
| Deterministic engine | Rule ops | `src/nova/agents/validator/deterministic.py` | `evaluate_deterministic_rule` | validator tests / fixtures | evaluation docs | Fixture MISMATCH cases |
| Contracts | MATCH/MISMATCH/UNCERTAIN | `src/nova/contracts/validation.py` | `ValidationCheck`, `ValidationOutcome` | `tests/contracts/` | contracts.md | Inspect API validation payload |
| Default rules | Presence required per field | `src/nova/application/rules.py` | `default_rules_for_document_type` | pipeline tests | features | GET `/v1/documents/{id}/validation` |
| Persistence | Append-only validations | `src/nova/application/validation_persistence.py`, models | `SqlValidationStore` | persistence / pipeline | database docs | Query `validations` table |
| Eval harness | Labeled cases | `src/nova/evaluation/validator/`, `fixtures/evaluation/validator/` | runners/metrics | `tests/evaluation/` | `docs/evaluation/validator-evaluation.md` | `scripts/run_full_evaluation.py` |

**UI:** Document page → Validation checks table (`frontend/src/components/ValidationChecks.tsx`) shows Result / Reason / Expected / Actual.

---

## Deliverable 2C — Router / Decision

| Requirement | Actual implementation | Path | Class / function | Test | Documentation | Third-party verify |
|-------------|----------------------|------|------------------|------|---------------|-------------------|
| Router service | Policy-first decide | `src/nova/router/service.py` | `RouterService.decide` | `tests/router/` | `docs/agents/router.md` | Decision eval FA=0 |
| Safety constraints | Block AUTO_APPROVE | `src/nova/router/constraints.py` | `evaluate_safety_constraints` | `tests/router/test_router_safety.py` | trust-model | Force mismatch → not AUTO_APPROVE |
| Contracts | DecisionKind + DecisionResult | `src/nova/contracts/routing.py` | `DecisionKind`, `_auto_approve_safety` | `tests/contracts/test_decision_safety.py` | contracts.md | Schema forbids failsafe AUTO_APPROVE |
| Persistence | Append-only decisions | `src/nova/router/persistence.py` | `DecisionRepository` | `tests/router/test_decision_persistence.py` | schema | GET decision endpoint |
| Advisory LLM | Optional; non-authoritative | `src/nova/router/llm.py` | `RouterLlmPort`, `NullRouterLlm` | router tests | router.md | Unsafe LLM AUTO_APPROVE overridden |
| Eval | Decision cases | `fixtures/evaluation/decision/`, `src/nova/evaluation/decision/` | runner | `tests/evaluation/test_decision_evaluation.py` | `docs/evaluation/reports/decision-eval-latest.json` | Open JSON: `false_auto_approve_count: 0` |

**UI:** `frontend/src/components/DecisionPanel.tsx` — decision badge + rationale.

---

## Deliverable 2D — Storage + Query

| Requirement | Actual implementation | Path | Class / function | Test | Documentation | Third-party verify |
|-------------|----------------------|------|------------------|------|---------------|-------------------|
| ORM models | Customers→shipments→documents→AI history | `src/nova/persistence/models.py` | `Document`, `ExtractedFieldRow`, `ValidationRecordRow`, `DecisionRecord`, … | `tests/integration/test_migrations.py` | `docs/database/` | `\dt` after alembic upgrade |
| Migrations | 0001–0004 | `alembic/versions/` | heads at `0004_phase7_pipeline` | CI migration step | deployment docs | `alembic current` |
| Repositories | Data access | `src/nova/persistence/repositories.py` | `NovaRepository` | API/pipeline tests | — | — |
| Ingestion + auto pipeline | Upload → store → orchestrate | `src/nova/application/ingestion.py` | `IngestionService`, `_run_pipeline` | `tests/api/test_documents_api.py`, `tests/pipeline/` | `docs/features/document-ingestion.md` | POST `/v1/documents` → DECIDED |
| Pipeline orchestrator | Extract→validate→route | `src/nova/application/pipeline.py` | `PipelineOrchestrator.run` | `tests/pipeline/test_pipeline_e2e.py` | `docs/architecture/end-to-end-pipeline.md` | Follow run_id in UI |
| Document storage | Local filesystem | `src/nova/documents/storage/local.py` | `LocalFilesystemStorage` | documents tests | ADR-0006 | Files under `DOCUMENT_STORAGE_PATH` |
| NL query service | Intent → repository | `src/nova/query/service.py` | `QueryService.answer` | `tests/query/` | `docs/api/query-interface.md` | POST `/v1/query` |
| Classifier / security | No SQL | `src/nova/query/classifier.py` | `security_reject`, `classify_intent` | `tests/query/test_query_security.py` | `docs/security/query-api.md` | Ask `SELECT * FROM…` → UNSUPPORTED |
| Executors | Allow-listed intents | `src/nova/query/executors.py` | `_list_shipments_by_decision`, … | `tests/query/test_query_supported.py` | query-interface | Ask HUMAN_REVIEW list; **no “this week” filter** |
| Query contracts | Intent enum | `src/nova/contracts/query.py` | `QueryIntentName` | `tests/contracts/test_query_schemas.py` | api contracts | Inspect enum — no weekly count intent |

**UI:** `frontend/src/pages/QueryPage.tsx`.

**Example verify “flagged” (PARTIAL):**

```text
Question: which shipments are in HUMAN_REVIEW?
→ LIST_SHIPMENTS_BY_DECISION (no calendar week filter)
```

---

## Deliverable 2E — Minimal UI

| Requirement | Actual implementation | Path | Component | Test | Documentation | Third-party verify |
|-------------|----------------------|------|-----------|------|---------------|-------------------|
| App shell / routes | React Router | `frontend/src/App.tsx` | pages | Vitest | `docs/architecture/frontend.md`, `docs/features/operations-ui.md` | Open http://localhost:8080 |
| Dashboard / pipeline counts | Ops summary | `frontend/src/pages/DashboardPage.tsx` | — | `DashboardPage.test.tsx` | ops UI docs | Create demo customer → Load dashboard |
| Upload | PDF/text only | `frontend/src/pages/UploadPage.tsx` | `ACCEPTED_TYPES` | `UploadPage.test.tsx` | demo-runbook | Try image → client reject |
| Document detail | Status, extraction, validation, decision | `frontend/src/pages/DocumentPage.tsx` | FieldTable, ValidationChecks, DecisionPanel | `DocumentPage.test.tsx` | ui-demo.md | After upload, open document link |
| Field confidence/evidence | Table | `frontend/src/components/FieldTable.tsx`, `EvidenceList.tsx` | — | via DocumentPage tests | — | Visual check |
| Real document body | **Not shown** | DocumentPage meta only; API `download_url: null` | ingestion `_response` content block | — | — | Confirm no preview/iframe |
| Shipment page | Shipment linkage | `frontend/src/pages/ShipmentPage.tsx` | — | — | — | Navigate from document |
| API client | Real backend | `frontend/src/api/*.ts` | `getDocument`, etc. | helpers | frontend README | Network tab → `/v1/...` |

---

## Deliverable 3 — Technical write-up inputs (scattered)

| Requirement | Closest artifact | Path | How to verify |
|-------------|------------------|------|---------------|
| Architecture diagram | ASCII | `ARCHITECTURE.md` | Read; not a single D3 PDF/MD write-up |
| Data flow / state | Pipeline architecture | `docs/architecture/end-to-end-pipeline.md` | Cross-check with `pipeline.py` |
| Failure modes | Failure testing philosophy | `docs/testing/failure-testing.md` | Confirm no “three nastiest” section |
| Testing evidence | Eval reports + CI | `docs/evaluation/reports/`, `.github/workflows/ci.yml` | Open JSON reports; check CI green on PR |
| Observability | Logs/metrics | `docs/observability/`, `src/nova/observability/` | `curl /metrics`, inspect logs |
| Cost / latency | Philosophy + bench script | `docs/testing/performance-testing.md`, `scripts/benchmark_pipeline.py` | Run bench locally (MockLLM only) |
| One week vs one day | **Missing** | — | Grep fails |

---

## Cross-cutting

| Area | Path | Key entry | Tests | Docs | Verify |
|------|------|-----------|-------|------|--------|
| API routes | `src/nova/api/routes/__init__.py`, `app.py` | FastAPI app | `tests/api/` | `docs/api/endpoints.md` | OpenAPI / curl |
| Config | `src/nova/config/__init__.py` | `Settings` | unit | `docs/deployment/configuration.md` | `.env.example` |
| Docker | `Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` | api/db/web | CI image build | `docs/deployment/local.md` | `docker compose up` |
| CI | `.github/workflows/ci.yml` | jobs | itself | `docs/deployment/ci-cd.md` | GitHub Actions |
| Demo fixtures | `fixtures/demo/` | `synthetic_invoice_*.txt`, `synthetic_bol_clean.txt` | demo smoke (manual) | `fixtures/demo/README.md`, `docs/operations/demo-runbook.md` | Upload clean + messy |
| Full eval script | `scripts/run_full_evaluation.py` | — | evaluation tests | evaluation README | `PYTHONPATH=src python scripts/run_full_evaluation.py` |
| Security baseline | `SECURITY.md`, `docs/security/` | — | secret script | baseline.md | `./scripts/check-secret-patterns.sh` |

---

## Assignment field → code presence cheat sheet

| GoComet field | `fields.py`? | Heuristic aliases? | Typical demo |
|---------------|--------------|--------------------|--------------|
| consignee_name | Yes (BOL) | Yes | BOL fixture |
| hs_code | **No** | **No** | — |
| port_of_loading | Yes (BOL) | Yes | BOL fixture |
| port_of_discharge | Yes (BOL) | Yes | BOL fixture |
| incoterms | **No** | **No** | — |
| description_of_goods | **No** | **No** | Text exists in invoice fixture but **not extracted** |
| gross_weight | **No** | **No** | Text exists in invoice fixture but **not extracted** |
| invoice_number | Yes (INVOICE) | Yes | Invoice fixture |

---

## Recommended reviewer path (30 minutes)

1. Read `docs/audits/gocomet-final-rubric-audit.md` (verdict + blockers).
2. Open `src/nova/extraction/fields.py` and `src/nova/documents/limits.py`.
3. `docker compose up --build` → demo-runbook clean invoice → Document UI.
4. Confirm: fields/confidence/validation/decision **visible**; document body **not** visible; image upload **fails**.
5. Run `PYTHONPATH=src python scripts/run_full_evaluation.py` → FA=0.
6. Search repo for `FDE` / `System of Outcomes` / `hs_code` → expect empty (submission gaps).
