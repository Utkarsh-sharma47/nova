# Requirement traceability

Maps requirements to architecture, contracts, planned implementation phase, tests, and evidence. Update when phases land. No P0 Part 1 requirement may disappear during architecture design.

**Legend:** Arch = design docs/ADRs · Contract = typed I/O or API · Impl = implementation phase · Test = planned verification · Evidence = artifact location

| REQ ID | Architecture | Contract | Planned impl phase | Test | Evidence |
|--------|--------------|----------|--------------------|------|----------|
| REQ-PROD-001–004 | `docs/product/*`, principles, system-architecture | — | 1 (docs) / 3–6 (runtime) | Doc review | Product + architecture docs |
| REQ-EXT-001 | Ingestion port, API ingest | `POST /v1/documents`, ExtractionRequest | 3 | Integration + failure | `docs/api/contracts.md`, samples |
| REQ-EXT-002 | Extractor agent | ExtractionResult / ExtractedField | 3 | Unit + golden | `docs/agents/extractor.md`, `src/nova/contracts/extraction.py` |
| REQ-EXT-003 | Confidence model | `confidence` on ExtractedField | 3 | Unit + eval | contracts + eval metrics |
| REQ-EXT-004 | Evidence model | `Evidence[]` | 3 | Unit + review UX | contracts + UI checklist (Ph6) |
| REQ-EXT-005 | Evaluation datasets | — | 5 | Eval harness | `docs/evaluation/datasets.md`, fixtures |
| REQ-EXT-006 | Failure isolation | StageError / ErrorResponse | 3–4 | Failure tests | `docs/testing/failure-testing.md` |
| REQ-VAL-001 | Validator + CustomerRule | ValidationRequest/Result | 4 | Unit + fixtures | `docs/agents/validator.md`, DB rules |
| REQ-VAL-002–004 | Validation outcomes | MATCH/MISMATCH/UNCERTAIN | 4 | Golden | contracts + golden cases |
| REQ-VAL-005 | Deterministic vs LLM boundary | `ValidationCheck.deterministic` | 2–4 | Design + unit | ADR-0010, validator doc |
| REQ-VAL-006 | Auditable validation | Validation + AuditEvent | 4–5 | Integration | schema + audit-model |
| REQ-ROUTER-001–003 | Router decisions | DecisionResult enums | 4 | Unit + eval | `docs/agents/router.md` |
| REQ-ROUTER-004 | Explicit policy | RoutingPolicySnapshot | 2–4 | Design + tests | router + routing contracts |
| REQ-ROUTER-005 | Fail-safe routing | safety constraints | 4 | Failure tests | trust-model + failure catalog |
| REQ-DATA-001 | Persistence architecture | DB schema | 5 | Integration | `docs/database/*` |
| REQ-DATA-002 | 1:N documents | schema relationships | 2–5 | Schema review | ERD + relationships.md |
| REQ-DATA-003 | Idempotent writes | Idempotency-Key + DB keys | 5 | Integration | api/idempotency + schema |
| REQ-DATA-004 | Retention/PII policy | security baseline | 1–5 | Doc review | `docs/security/` |
| REQ-QUERY-001 | Query API | GET shipment/document | 5–6 | Integration | api/contracts |
| REQ-QUERY-002–003 | NL query, grounded | `POST /v1/query` | 6 | Eval + integration | query-interface.md (**no LLM SQL**) |
| REQ-UI-001–003 | Frontend ADR-0009 | — | 6 | Manual/smoke | ADR-0009 + UI feature docs |
| REQ-AI-001–003 | Agent architecture | Extractor/Validator/Router contracts | 3–4 | Contract tests | `docs/agents/*`, `tests/contracts/` |
| REQ-AI-004 | No silent fabrication | FieldPresence invariants | 3–4 | Contract + eval | extraction.py validators |
| REQ-AI-005 | Timeouts/retries/cost | timeout_ms + UsageMetrics | 3–4 | Unit/integration | agent docs + contracts |
| REQ-AI-006 | Model/prompt versions | ModelMetadata | 3–5 | Integration | trust-model prompt governance |
| REQ-OBS-001–004 | Observability ADR-0007 | TraceContext / health | 3–5 | Integration | observability architecture |
| REQ-TEST-001–004 | Testing architecture | contract tests (now) | 1 / 2 / 3+ | CI | `docs/testing/*`, pytest |
| REQ-DEPLOY-001–004 | Deploy ADR-0008 + CI | Docker Compose skeleton | 1 / 2 / 7 | CI | workflows + ci-cd.md |
| REQ-DOC-001–004 | Docs system + ADRs | — | 1–2 | Docs script | `docs/**`, ADR-0001…0010 |
| REQ-SEC-001–005 | Security baseline + arch | API auth assumptions | 1–5 | Secret scan + review | security docs + CI |
| REQ-SUBMISSION-001–003 | Demo/runbook (future) | — | 7 | Demo | ops runbook |
| REQ-PART2-001–007 | Extension points | related_extractions, stubs | 1–2 design | Design review | part2-extension-points + schema stubs |

## Traceability rules

1. Every P0 Part 1 requirement must have a design pointer before coding starts.
2. Every implemented requirement must have a test pointer before claiming done.
3. Evidence must be reproducible by a reviewer from the repository or documented commands.
4. Architecture phases must **not** drop requirements; defer with explicit status only.

## Phase 2 coverage check

All 68 inventory requirements retain a design/contract/test pointer above. Runtime implementation remains Phases 3–7 except contract schema encoding and CI for contracts (Phase 2).

## Phase 3 implementation evidence

| Requirement | Implementation | Test | Reproducible evidence |
|-------------|----------------|------|-----------------------|
| REQ-EXT-001 | `nova.api.routes`, `nova.application.ingestion`, `nova.documents` | `tests/api/test_documents_api.py`, `tests/documents/` | Authenticated multipart upload returns 202; normalized `DocumentContent` and persisted IDs |
| REQ-EXT-006 | Typed processor/domain errors, orphan cleanup, global safe handlers | `tests/documents/test_contracts.py`, API failure and ingestion unit tests | Corrupt/unsupported input is structured; database failures do not leave blobs; HTTP bodies omit internals |
| REQ-DATA-001 | SQLAlchemy core ingestion entities + retrieval API | API + migration integration | Customer/shipment/document/version/run tables and GET projections |
| REQ-DATA-002 | Shipment-to-documents 1:N model | API + migration integration | No uniqueness constraint on `documents.shipment_id` |
| REQ-DATA-003 | Principal/key/fingerprint idempotency records with unique-violation recovery | API replay/conflict and concurrent-ingestion tests | Same request replays, concurrent loser re-reads winner, changed content returns 409 |
| REQ-QUERY-001 (partial) | Document and shipment GET endpoints | API retrieval tests | Persisted ingestion metadata is queryable; validation/decision reads remain deferred |
| REQ-OBS-001–002 | JSON formatter, request/trace middleware, `/metrics` | API header and metrics tests | Correlation headers, structured fields, Prometheus request count/latency; no agent-stage tracing yet |
| REQ-OBS-004 (partial) | Safe classified HTTP errors and schema/storage readiness | API readiness and failure tests | DB-down, missing-schema, and storage failures are visible without connection details |
| REQ-TEST-001,003–004 | Unit/API/integration plus retained contract suite | `tests/` | `ruff check src tests`, `mypy`, `pytest -q` |
| REQ-DEPLOY-003–004 | Non-root image, bounded DB wait, Compose, CI PostgreSQL | clean/repeated migration validation and Docker build | `Dockerfile`, `scripts/entrypoint.sh`, `docker-compose.yml`, CI workflow |
| REQ-DOC-001–003 | Phase 3 feature, API, architecture, ops docs | docs structure check | Repository documentation listed in this row |
| REQ-SEC-001–004 | Env-only auth, safe logs, upload controls/storage confinement | unit/API security assertions | No committed secret; path traversal/type/size/auth tests |

Not claimed in Phase 3: REQ-EXT-002–005 and REQ-AI-001–006 runtime agent
behavior. Frozen Phase 2 contracts remain available, but no Extractor,
Validator, Router, or LLM implementation exists.

## Phase 6 Router / decision evaluation evidence

| Requirement | Implementation | Test | Reproducible evidence |
|-------------|----------------|------|-----------------------|
| REQ-ROUTER-001–003 | `nova.router.RouterService` dispositions | `tests/agents/router/`, `tests/router/`, decision eval | AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST on labeled cases |
| REQ-ROUTER-004 | `RoutingPolicySnapshot` + constraint engine | unit + eval | Versioned policy fields and `safety_constraints_applied` |
| REQ-ROUTER-005 | Failsafe / timeout / malformed / LLM override | failure + critical_safety eval | Never AUTO_APPROVE on failure paths |
| REQ-TEST-002 | Golden / fixture routing | `fixtures/evaluation/decision/` | Fixed regression revision `2026-08-25.r1` |
| REQ-AI-004 (routing) | No silent uncertainty→approve | critical_safety cases | False AUTO_APPROVE rate 0.0 on regression set |
| REQ-SUBMISSION-002 (partial) | Eval report via harness | `tests/evaluation/test_decision_evaluation.py` | Metrics include false AUTO_APPROVE rate |

Detail: [`docs/evaluation/decision-evaluation.md`](../evaluation/decision-evaluation.md),
[`docs/agents/router.md`](../agents/router.md).
