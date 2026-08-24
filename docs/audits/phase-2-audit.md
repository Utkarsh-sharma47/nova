# Phase 2 audit — Technology Architecture + Domain Contracts

**Auditor role:** Principal Engineer (integration)  
**Branch:** `feature/phase-2-integration`  
**Date:** 2026-08-25  
**Scope:** Integrate and audit Phase 2 specialist workstreams; freeze blueprint for Phase 3+  
**Verdict:** **PASS** (no unresolved CRITICAL or HIGH findings after integration fixes)

---

## 1. Executive summary

Phase 2 freezes Nova’s technology stack, domain/persistence design, AI agent contracts, HTTP API contracts, testing/evaluation architecture, and a Pydantic contract package with CI. Application business logic, agents, ORM, and UI are **not** implemented (by design).

Specialist branches were merged semantically (not ours/theirs):

| Workstream | Branch | Integrated |
|------------|--------|------------|
| AI contracts / trust | `feature/phase-2-ai-contracts` | Yes |
| Domain / database | `feature/phase-2-domain-database` | Yes |
| HTTP API contracts | `feature/phase-2-api-contracts` | Yes |
| Testing / evaluation | `feature/phase-2-testing-evaluation` | Yes |
| Stack + system architecture + Pydantic | `feature/phase-2-architecture` | Yes |

Integration fixes resolved ADR collisions, API path/idempotency contradictions, and CRITICAL agent↔Pydantic gaps (`FieldPresence`, `run_id`, extraction status, evidence lists). Cross-layer mapping is normative in [`docs/architecture/contract-alignment.md`](../architecture/contract-alignment.md).

---

## 2. Technology decisions

| Layer | Choice | ADR | Rationale present |
|-------|--------|-----|-------------------|
| Backend | Python 3.12+, Pydantic, SQLAlchemy, Alembic, pytest, Ruff, MyPy | [0002](../decisions/0002-backend-stack.md) | Yes |
| Database | PostgreSQL 16 | [0003](../decisions/0003-database.md) | Yes |
| API | FastAPI | [0004](../decisions/0004-api-framework.md) | Yes |
| AI | Provider-agnostic `LLMPort` | [0005](../decisions/0005-ai-provider-abstraction.md) | Yes |
| Documents | Pluggable processor/OCR port | [0006](../decisions/0006-document-processing.md) | Yes |
| Observability | Structured logs + metrics + health | [0007](../decisions/0007-observability.md) | Yes |
| Deployment | Docker / Compose | [0008](../decisions/0008-deployment.md) | Yes |
| Frontend | React + TypeScript + Vite | [0009](../decisions/0009-frontend-stack.md) | Yes |
| AI trust / contracts | Typed agents + trust model | [0010](../decisions/0010-ai-agent-contracts-and-trust-model.md) | Yes |

Index: [`docs/architecture/technology-stack.md`](../architecture/technology-stack.md).

---

## 3. Architecture audit

| Check | Status |
|-------|--------|
| Backend stack selected | Pass |
| Database selected | Pass |
| API architecture selected | Pass |
| Frontend architecture selected | Pass |
| AI abstraction selected | Pass |
| Deployment architecture selected | Pass |
| Observability architecture selected | Pass |
| System / layering / AI architecture docs | Pass |
| Part 2 extension points preserved | Pass |

---

## 4. Domain audit

Entities defined in [`docs/database/domain-model.md`](../database/domain-model.md):

Customer, Shipment, Document, DocumentVersion, ExtractedField, CustomerRule, Validation, ValidationCheck, Decision, AuditEvent (+ supporting VerificationRun / ModelCallMetadata).

| Check | Status |
|-------|--------|
| Consistent entity catalog | Pass |
| Relationships / ER | Pass (`relationships.md`) |
| 1:N documents per shipment | Pass |
| Part 2 stubs (email, drafts, approvals, outbound) | Pass (design only) |
| Data classification (business / AI / derived / audit) | Pass |

Lifecycle projection vs API status strings clarified: DB domain enums are authoritative; API statuses are projections ([contract-alignment.md](../architecture/contract-alignment.md)).

---

## 5. AI contract audit

| Contract | Documented | Encoded in Pydantic | Notes |
|----------|------------|---------------------|-------|
| ExtractionRequest / ExtractionResult | Pass | Pass | `FieldPresence` + evidence invariants enforced |
| ValidationRequest / ValidationResult | Pass | Pass | Part 2 `related_extractions` reserved |
| RoutingRequest / DecisionResult | Pass | Pass | `allow_auto_approve_on_unknown=false` default |
| ErrorResponse | Pass | Pass | Maps to HTTP envelope |
| AuditEvent | Pass | Pass | Append-only intent in DB audit model |

Field naming / IDs / timestamps / confidence / evidence / uncertainty / errors / versioning: mapped in [contract-alignment.md](../architecture/contract-alignment.md).

---

## 6. API audit

| Check | Status |
|-------|--------|
| Endpoint consistency (`/v1`…) | Pass (normalized; `/api/v1` rejected) |
| Error model | Pass |
| HTTP semantics (202 ingest) | Pass |
| Idempotency (`Idempotency-Key` required on ingest) | Pass |
| Security assumptions (API key Part 1) | Pass (documented) |
| Query safety (no LLM SQL) | Pass (`query-interface.md`) |

---

## 7. Database audit

| Check | Status |
|-------|--------|
| Referential integrity | Pass (documented) |
| Indexes | Pass |
| Uniqueness / soft-delete partial uniques | Pass |
| Auditability | Pass |
| Multiple documents per shipment | Pass |
| Future cross-document validation | Pass (schema + validation contract) |
| Idempotency keys | Pass |

Migrations/ORM: intentionally deferred to Phase 5.

---

## 8. Testing / evaluation audit

| Layer | Spec | Implementation |
|-------|------|----------------|
| Unit | Planned Ph3+ | Not yet (correct) |
| Contract | Spec + code | `tests/contracts/` + CI |
| Integration | Spec + DB test plan | Not yet |
| E2E | Spec | Not yet |
| AI evaluation | Framework/metrics/datasets | Harness not built |
| Regression | Mandatory policy | Not automated yet |
| Failure | Catalog | Not yet |
| Performance | Spec | Tooling not yet |

---

## 9. Security audit

| Topic | Status |
|-------|--------|
| Secrets / `.env` | Pass (gitignore + CI scan) |
| No secrets in examples | Pass (placeholders) |
| NL query no arbitrary SQL | Pass (normative) |
| Document sensitivity | Pass (baseline + architecture) |
| Auth assumptions Part 1 | Documented (API key); full RBAC later |

---

## 10. Part 2 compatibility audit

| Extension | Design obligation met? |
|-----------|------------------------|
| Email / file ingestion ports | Yes |
| Multi-document shipments | Yes |
| Cross-document validation context | Yes (`related_extractions`, validation port) |
| Draft replies / outbound | Stub tables + CommunicationPort reserved |
| Human approval | Append-only decisions + approval stub |

Part 2 features are **not** implemented.

---

## 11. Traceability audit

[`docs/requirements/traceability.md`](../requirements/traceability.md) updated: Requirement → Architecture → Contract → Planned phase → Test → Evidence for all inventory categories (68 REQs). No requirement dropped during architecture design.

---

## 12. Findings

### Resolved during integration (were CRITICAL/HIGH)

1. ADR number collision (AI contracts vs backend both `0002`) → AI trust is **ADR-0010**.
2. Dual PostgreSQL ADRs → single **ADR-0003**.
3. Agent `FieldPresence` missing from Pydantic → added with invariants.
4. `run_id` vs `trace_id` vs `verification_run_id` undefined → mapping doc + `run_id` on TraceContext.
5. Extraction `SUCCEEDED` vs `COMPLETED` → canonical SUCCEEDED; COMPLETED alias normalized.
6. API `/v1` vs `/api/v1` and optional vs required Idempotency-Key → `/v1` + required + 202.
7. Provider error 502 vs 503 → **502** for Part 1 API normative mapping.

### Residual (accepted for Phase 2)

| ID | Severity | Finding | Disposition |
|----|----------|---------|-------------|
| F-01 | MEDIUM | DB column names (`field_key`, `is_missing`) differ from Pydantic names | Documented mapping; OK until ORM Phase 5 |
| F-02 | MEDIUM | Lifecycle enum vocabulary differs between domain-model and illustrative lifecycle doc | Domain-model authoritative; noted in alignment doc |
| F-03 | LOW | Frontend/UI detailed wireframes absent | Correctly deferred to Phase 6 + ADR-0009 |
| F-04 | LOW | Evaluation thresholds not numeric | Correct: calibration targets only |
| F-05 | LOW | Architecture specialist self-audit claims “Done” before integration | Superseded by this audit |

---

## 13. Severity summary

| Severity | Open count |
|----------|------------|
| CRITICAL | **0** |
| HIGH | **0** |
| MEDIUM | 2 (accepted mappings) |
| LOW | 3 |

---

## 14. Required fixes

**None blocking Phase 2 exit.** Recommended follow-ups (Phase 3+):

1. Generate OpenAPI from FastAPI once routes exist; keep aligned with `docs/api/contracts.md`.
2. Alembic migrations mirroring `schema-design.md`.
3. Implement agent runtimes against `src/nova/contracts` without weakening FieldPresence rules.
4. Stand up evaluation harness per `docs/evaluation/*`.

---

## 15. Phase 3 readiness

| Criterion | Ready? |
|-----------|--------|
| Stack frozen via ADRs | Yes |
| Contracts implementable without new architecture debates | Yes (with alignment doc) |
| CI runs real docs + Python contract checks | Yes |
| Ingestion + Extractor can start | Yes |
| No CRITICAL/HIGH open | Yes |

**Phase 3 may proceed** on a feature branch implementing ingestion + Extractor against these contracts.

---

## Verification evidence (commands run)

See integration commit message / final report for exact command outputs. Checks intended:

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
pip install -e ".[dev]"
ruff check src tests
mypy
pytest -q
```
