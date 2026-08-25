# Final GoComet file-location map

Requirement → exact code → tests → demo evidence → status.

Companion verdict: [final-gocomet-submission-audit.md](./final-gocomet-submission-audit.md).

Status values: **PASS** | **PARTIAL** | **FAIL** | **N/A**

---

## Deliverable 1 — PRD

| Requirement | Exact file | Implementation / location | Test / evaluation | Demo / UI evidence | Status |
|-------------|------------|---------------------------|-------------------|--------------------|--------|
| Nova ≤200 words | `docs/submission/prd.md` §1 | Narrative section | Doc review | Read PRD | PASS |
| FDE ≤200 words | `docs/submission/prd.md` §2 | Narrative section | Doc review | Read PRD | PASS |
| System of Outcomes ≤200 words | `docs/submission/prd.md` §3 | Narrative + vs Record/Engagement | Doc review | Read PRD | PASS |
| Diff System of Record | `docs/submission/prd.md` §3 | Explicit subsection | Doc review | Read PRD | PASS |
| Diff System of Engagement | `docs/submission/prd.md` §3 | Explicit subsection | Doc review | Read PRD | PASS |
| Failure modes | `docs/submission/prd.md` §4 | Table of modes | Doc review | Read PRD | PASS |
| CG first-5-minutes | `docs/submission/prd.md` §5 | CG operator subsection | Manual demo | Demo runbook | PASS |
| Personas CG + SU | `docs/submission/prd.md` §5 | Two personas | Doc review | Read PRD | PASS |
| ≥5 JTBD | `docs/submission/prd.md` §5 | Six JTBD lines | Doc review | Read PRD | PASS |
| Three agents + why not 1/5 | `docs/submission/prd.md` §6 | Table + rationale | Doc review | Read PRD | PASS |
| Agent I/O + handoff | `docs/submission/prd.md` §6 | I/O table | Doc review | Read PRD | PASS |
| Crash recovery / persistence | `docs/submission/prd.md` §6 | Persistence bullets | Code: `pipeline.py`, models | Demo IDs survive refresh | PASS |
| LLM per agent / tradeoffs / vision / fallback / orchestration / structured output / trust / retries / offline+online | `docs/submission/prd.md` §6–7 | Matrix + metrics | Eval scripts | Read PRD | PASS |
| North-star + 5–8 metrics + Go/No-Go + 2-week plan | `docs/submission/prd.md` §7 | Metrics + roadmap | Doc review | Read PRD | PASS |

---

## Deliverable 2A — Extractor

| Requirement | Exact file | Implementation / location | Test / evaluation | Demo / UI evidence | Status |
|-------------|------------|---------------------------|-------------------|--------------------|--------|
| PDF input | `src/nova/documents/adapters/digital_pdf.py` | `DigitalPdfAdapter` | `tests/documents/` | Upload PDF | PASS |
| Image input PNG/JPEG | `src/nova/documents/adapters/raster_image.py`, `limits.py` | `RasterImageAdapter`; `SUPPORTED_MEDIA_TYPES` | `tests/documents/test_raster_image.py`, `tests/api/test_documents_api.py::test_accepts_png_and_serves_content` | Upload PNG | PASS |
| Vision LLM path | `src/nova/llm/port.py` `LLMImagePart`; `src/nova/llm/openai_compatible.py` `OpenAICompatibleLLM`; `extraction/service.py` passes images | Unit: `tests/llm/test_openai_compatible.py` | Live only with key | PASS (path); live quality **PARTIAL** without keyed run |
| Structured JSON | `src/nova/contracts/extraction.py`, `extraction/parsing.py` | `ExtractionResult` / `ExtractedField` | `tests/extraction/`, `tests/contracts/` | Field table | PASS |
| Field `consignee_name` | `src/nova/extraction/fields.py` `ASSIGNMENT_FIELDS` | Always in invoice/BoL required lists | `tests/extraction/test_assignment_fields.py`, extractor eval | Document page | PASS |
| Field `hs_code` | same | same | same | same | PASS |
| Field `port_of_loading` | same | same | same | same | PASS |
| Field `port_of_discharge` | same | same | same | same | PASS |
| Field `incoterms` | same | same | same | same | PASS |
| Field `description_of_goods` | same | same | same | same | PASS |
| Field `gross_weight` | same | same | same | same | PASS |
| Field `invoice_number` | same | same | same | same | PASS |
| Confidence every field | `contracts/extraction.py` `ExtractedField.confidence` | Present; null allowed when not KNOWN | Contract + heuristic tests | FieldTable confidence column | PASS |
| Evidence when applicable | `ExtractedField.evidence`; heuristic + normalize | KNOWN requires evidence | Fabrication tests | EvidenceList | PASS |
| Missing stays missing / no fabrication | `heuristic.py`, `parsing.py`, extractor eval | Never invent | `fabrication_count=0` | MISSING rows | PASS |

---

## Deliverable 2B — Validator

| Requirement | Exact file | Implementation / location | Test / evaluation | Demo / UI evidence | Status |
|-------------|------------|---------------------------|-------------------|--------------------|--------|
| Customer rule set | `src/nova/application/rules.py` `default_rules_for_document_type`; `CustomerRuleSnapshot` | Defaults + requestable rules | Validator eval fixtures | Validation table | PASS (authoring UI **PARTIAL**) |
| Field-by-field MATCH/MISMATCH/UNCERTAIN | `src/nova/agents/validator/` | Deterministic + agent | `fixtures/evaluation/validator/`, `unsafe_match_count=0` | `ValidationChecks.tsx` | PASS |
| Expected vs found | `ValidationCheck.expected_value` / `actual_value` | Engine + persistence | Eval + UI columns Expected/Actual | Document page | PASS |
| Uncertainty surfaced | outcomes + UI highlight | `DocumentPage` panel highlight | Vitest DocumentPage | Visual UNCERTAIN | PASS |
| No silent approval | Router + validator invariants | Cannot upgrade MISMATCH | Safety tests + FA=0 | Decision not AUTO on uncertain | PASS |

---

## Deliverable 2C — Router

| Requirement | Exact file | Implementation / location | Test / evaluation | Demo / UI evidence | Status |
|-------------|------------|---------------------------|-------------------|--------------------|--------|
| AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST | `src/nova/contracts/routing.py` `DecisionKind`; `router/service.py` | Exactly one disposition | `tests/router/`, decision eval | `DecisionPanel.tsx` | PASS |
| Reasoning | `DecisionResult.reasons` / rationale projection | Router + API | Tests + UI | Decision panel | PASS |
| Fail-closed / FA=0 | `router/constraints.py` | Blocks unsafe AUTO | `false_auto_approve_count=0` | No false approve in eval | PASS |

---

## Deliverable 2D — Storage + Query

| Requirement | Exact file | Implementation / location | Test / evaluation | Demo / UI evidence | Status |
|-------------|------------|---------------------------|-------------------|--------------------|--------|
| Persistent DB | `src/nova/persistence/models.py`, Alembic `0001`–`0004` | PostgreSQL 16 | Migration CI / integration | Compose db | PASS |
| Verified outputs stored | append-only extraction/validation/decision tables | Persistence services | Pipeline e2e | API GET | PASS |
| NL grounded query | `src/nova/query/service.py`, `classifier.py`, `executors.py` | Allow-listed intents | `tests/query/` | Query page | PASS |
| “Flagged this week” | `classifier._time_range_from_text`, `executors._list_shipments_by_decision` | `time_range.preset=this_week` | `tests/query/test_query_time_range.py` | Ask in Query UI | PASS |
| No arbitrary SQL / security | `classifier.security_reject` | Rejects SQL/schema/prompt abuse | `tests/query/test_query_security.py` | Injection → unsupported | PASS |

---

## Deliverable 2E — UI

| Requirement | Exact file | Implementation / location | Test / evaluation | Demo / UI evidence | Status |
|-------------|------------|---------------------------|-------------------|--------------------|--------|
| Real document preview | `frontend/src/components/DocumentPreview.tsx`; `GET /v1/documents/{id}/content` in `api/routes/__init__.py` | Auth blob stream | DocumentPage Vitest + API content test | Document page | PASS |
| Fields / confidence / validation / decision / reasoning / status / IDs | `DocumentPage.tsx`, `FieldTable.tsx`, `ValidationChecks.tsx`, `DecisionPanel.tsx` | Live API client | Vitest | Demo runbook | PASS |
| Real backend state | `frontend/src/api/*` | No business mocks | Network `/v1/*` | DevTools | PASS |

---

## Deliverable 3 — Technical write-up

| Requirement | Exact file | Status |
|-------------|------------|--------|
| Architecture, agents, state, 3 failures, observability, cost, latency, one-week vs one-day | `docs/submission/technical-writeup.md` | PASS |
| Architecture diagram | `docs/submission/architecture-diagram.md` | PASS |
| MEASURED / ESTIMATED / PLANNED labels | technical-writeup §8–9 | PASS |

---

## Cross-cutting

| Requirement | Exact file | Status |
|-------------|------------|--------|
| MockLLM default | `application/extraction.py` `build_default_llm` | PASS |
| Secrets not in git | `.env` gitignored; `scripts/check-secret-patterns.sh` | PASS |
| Production no `create_all` | Only tests use `Base.metadata.create_all`; app uses Alembic | PASS |
| Docker / health / ready / metrics | `docker-compose.yml`, routes | PASS (compose build **MEASURED**; remote deploy **N/A**) |
| CI | `.github/workflows/ci.yml` | PASS |
