# Requirements inventory

Stable requirement IDs for Nova. Do not renumber casually; deprecate and replace instead.

**Legend**

| Field | Values |
|-------|--------|
| Source type | `ASSIGNMENT` = from assignment brief; `ENGINEERING` = needed for safe production delivery |
| Priority | `P0` must-have for Part 1 · `P1` should-have Part 1 · `P2` Part 2 / later |
| Part | `1` · `2` · `Both` |
| Status | `documented` · `planned` · `in_progress` · `done` · `deferred` |

Planned implementation phases map to `docs/roadmap/roadmap.md`.

---

## REQ-PROD — Product / problem

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-PROD-001 | Nova verifies trade/shipping documents (e.g. invoice, Bill of Lading) as an operational system | ASSIGNMENT | P0 | 1 | Problem and solution docs describe operational verification, not generic chat | Phase 1 | Doc review | `docs/product/*` | documented |
| REQ-PROD-002 | System replaces expensive/error-prone manual email verification loops between shipper and validation team | ASSIGNMENT | P0 | 1 | Problem definition states manual workflow, pain points, desired outcome | Phase 1 | Doc review | `docs/product/problem-definition.md` | documented |
| REQ-PROD-003 | System must not auto-approve blindly when confidence or rules indicate risk | ASSIGNMENT | P0 | 1 | Router can emit HUMAN_REVIEW / AMENDMENT_REQUEST; principles forbid blind automation | Phase 1→4 | Design + later eval | Architecture + router specs | documented |
| REQ-PROD-004 | Human review remains available for uncertain or high-risk cases | ASSIGNMENT | P0 | Both | HUMAN_REVIEW is a first-class router decision; Part 2 adds approval UX | Phase 1→4 / Part 2 | Design review | Scope + extension points | documented |

---

## REQ-EXT — Extraction

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-EXT-001 | Accept trade/shipping document input for Part 1 (file/path or upload abstraction) | ASSIGNMENT | P0 | 1 | Document can be submitted into the Part 1 pipeline | Phase 3 | Integration | API/contract + sample run | planned |
| REQ-EXT-002 | Extractor Agent extracts required business fields from the document | ASSIGNMENT | P0 | 1 | Required field set returned for supported doc types | Phase 4 | Unit + golden | Extraction contract + samples | implemented (MockLLM) |
| REQ-EXT-003 | Each extracted field includes a confidence score | ASSIGNMENT | P0 | 1 | Confidence present on every extracted field (or explicit null with reason) | Phase 3 | Unit + eval | Schema + eval report | planned |
| REQ-EXT-004 | Each extracted field includes evidence/grounding (where in the document) | ASSIGNMENT | P0 | 1 | Evidence reference suitable for audit/review | Phase 3 | Unit + review UX | Schema + sample evidence | planned |
| REQ-EXT-005 | Provide at least one clean sample document and one messy/hard sample | ASSIGNMENT | P0 | 1 | Both samples checked in (or clearly licensed fixtures) and used in eval | Phase 5 | Eval harness | `fixtures/` + eval results | planned |
| REQ-EXT-006 | Extraction failures are isolated and reported without crashing the whole service | ENGINEERING | P0 | 1 | Failed extraction yields structured error / UNCERTAIN path | Phase 3–4 | Failure tests | Logs + API error shape | planned |

---

## REQ-VAL — Validation

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-VAL-001 | Validate extracted fields against customer-specific rules | ASSIGNMENT | P0 | 1 | Rules engine/agent applies per-customer rule set | Phase 4 | Unit + fixture rules | Rules format + tests | planned |
| REQ-VAL-002 | Produce validation result MATCH | ASSIGNMENT | P0 | 1 | MATCH emitted when rules satisfied within policy | Phase 4 | Unit | Golden cases | planned |
| REQ-VAL-003 | Produce validation result MISMATCH | ASSIGNMENT | P0 | 1 | MISMATCH emitted with field-level reasons | Phase 4 | Unit | Golden cases | planned |
| REQ-VAL-004 | Produce validation result UNCERTAIN | ASSIGNMENT | P0 | 1 | UNCERTAIN when confidence/evidence/rules insufficient | Phase 4 | Unit | Golden cases | planned |
| REQ-VAL-005 | Prefer deterministic validation for clear rule checks; use LLM reasoning only where appropriate | ENGINEERING | P0 | 1 | Design separates deterministic checks vs LLM-assisted judgment | Phase 2–4 | Design + tests | ADR + validator design | planned |
| REQ-VAL-006 | Validation output is auditable (inputs, rule IDs, outcomes) | ENGINEERING | P0 | 1 | Persisted validation record reconstructs decision basis | Phase 4–5 | Integration | DB/API audit fields | planned |

---

## REQ-ROUTER — Routing decisions

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-ROUTER-001 | Router Agent decides AUTO_APPROVE | ASSIGNMENT | P0 | 1 | AUTO_APPROVE only when policy thresholds met | Phase 4 | Unit + eval | Policy + golden | planned |
| REQ-ROUTER-002 | Router Agent decides HUMAN_REVIEW | ASSIGNMENT | P0 | 1 | HUMAN_REVIEW for uncertain/high-risk cases | Phase 4 | Unit + eval | Policy + golden | planned |
| REQ-ROUTER-003 | Router Agent decides AMENDMENT_REQUEST | ASSIGNMENT | P0 | 1 | AMENDMENT_REQUEST when corrections needed from shipper | Phase 4 | Unit + eval | Policy + golden | planned |
| REQ-ROUTER-004 | Routing policy is explicit and reviewable (not opaque prompt-only) | ENGINEERING | P0 | 1 | Policy documented; thresholds/testable conditions defined | Phase 2–4 | Design + tests | `docs/agents/` + tests | planned |
| REQ-ROUTER-005 | Router never silently upgrades risk to AUTO_APPROVE on tool/LLM failure | ENGINEERING | P0 | 1 | Fail-safe defaults to HUMAN_REVIEW or safe halt | Phase 4 | Failure tests | Chaos/failure fixtures | planned |

---

## REQ-DATA — Persistence

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-DATA-001 | Persist shipment / document / validation / decision records | ASSIGNMENT | P0 | 1 | CRUD/read path exists for core entities | Phase 5 | Integration | Schema + API | planned |
| REQ-DATA-002 | Data model supports multiple documents per shipment (even if Part 1 uses one) | ENGINEERING | P0 | Both | Schema allows 1:N documents without breaking Part 1 | Phase 2–5 | Schema review | ERD + migration | planned |
| REQ-DATA-003 | Writes are idempotent where re-processing the same document is possible | ENGINEERING | P1 | 1 | Re-submit does not create unbounded duplicates | Phase 5 | Integration | Idempotency keys/tests | planned |
| REQ-DATA-004 | Retention and PII handling policy documented (implementation may be minimal in Part 1) | ENGINEERING | P1 | Both | Security/ops docs state data handling expectations | Phase 1–5 | Doc review | `docs/security/` | documented |

---

## REQ-QUERY — Query layer

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-QUERY-001 | Provide a query layer over persisted data | ASSIGNMENT | P0 | 1 | Operators can retrieve shipments/docs/decisions | Phase 8 | Integration | API demos | implemented |
| REQ-QUERY-002 | Support natural-language query over persisted verification data | ASSIGNMENT | P0 | 1 | NL query returns grounded answers from persisted records | Phase 8 | Unit + integration | Query examples + traces | implemented |
| REQ-QUERY-003 | NL query must not invent facts not present in persisted data | ENGINEERING | P0 | 1 | Answers cite records or refuse when unknown | Phase 8 | Security + empty cases | Eval/adversarial + tests | implemented |

---

## REQ-UI — Operations UI

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-UI-001 | Provide a minimal B2B operations UI | ASSIGNMENT | P0 | 1 | UI supports core ops: submit/view docs, see extraction/validation/decision | Phase 6 | Manual + smoke | Screenshots + demo | planned |
| REQ-UI-002 | UI surfaces confidence, evidence, and validation outcomes for review | ENGINEERING | P0 | 1 | Reviewer can see why a decision was made | Phase 6 | Manual | UI checklist | planned |
| REQ-UI-003 | UI remains usable for HUMAN_REVIEW queue (even if approval actions are Part 2) | ENGINEERING | P1 | Both | Review list/detail readable in Part 1 | Phase 6 | Manual | UI checklist | planned |

---

## REQ-AI — Agents / LLM usage

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-AI-001 | Use an Extractor Agent for field extraction | ASSIGNMENT | P0 | 1 | Extractor is a distinct agent with typed I/O contract | Phase 3 | Contract tests | `docs/agents/` | planned |
| REQ-AI-002 | Use a Validator path for rule checking (agent and/or deterministic engine) | ASSIGNMENT | P0 | 1 | Validation stage is distinct and contract-tested | Phase 4 | Contract tests | `docs/agents/` | planned |
| REQ-AI-003 | Use a Router Agent for disposition decisions | ASSIGNMENT | P0 | 1 | Router is distinct with typed decision enum | Phase 4 | Contract tests | `docs/agents/` | planned |
| REQ-AI-004 | Confidence-aware prompting/post-processing; avoid hallucinated fields without flags | ENGINEERING | P0 | 1 | Missing/low-confidence fields marked; not silently invented as certain | Phase 3–4 | Eval | Eval report | planned |
| REQ-AI-005 | LLM calls have timeouts, retry limits, and cost controls | ENGINEERING | P0 | 1 | Configured limits; exhausted retries → safe failure path | Phase 3–4 | Unit/integration | Config + tests | planned |
| REQ-AI-006 | Prompts, models, and versions are recorded for reproducibility | ENGINEERING | P1 | 1 | Run metadata stores model/prompt version identifiers | Phase 3–5 | Integration | Trace/metadata | planned |

---

## REQ-OBS — Observability

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-OBS-001 | Structured logging across pipeline stages | ENGINEERING | P0 | 1 | JSON/structured logs with correlation/run IDs | Phase 3–5 | Integration | Log samples | planned |
| REQ-OBS-002 | Trace each document through extraction → validation → routing → persistence | ENGINEERING | P0 | 1 | Single run ID ties stage events together | Phase 3–5 | Integration | Trace demo | planned |
| REQ-OBS-003 | Record token/cost metrics per run where LLM used | ENGINEERING | P1 | 1 | Cost fields available for sample runs | Phase 3–5 | Integration | Metrics sample | planned |
| REQ-OBS-004 | Failure modes are visible (timeouts, parse errors, rule engine errors) | ENGINEERING | P0 | 1 | Errors classified and queryable | Phase 4–5 | Failure tests | Error taxonomy doc | planned |

---

## REQ-TEST — Testing

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-TEST-001 | Automated unit/integration tests for non-LLM deterministic logic | ENGINEERING | P0 | 1 | CI runs real tests; failures fail the build | Phase 3+ | CI | CI logs | planned |
| REQ-TEST-002 | Golden / fixture tests for validation and routing policies | ENGINEERING | P0 | 1 | Fixture suite covers MATCH/MISMATCH/UNCERTAIN and all router outcomes | Phase 4–5 | CI | Test report | planned |
| REQ-TEST-003 | No fake success-only tests | ENGINEERING | P0 | 1 | Tests assert behavior; CI contains no placeholder always-green app tests | Phase 1+ | Review | CI config | documented |
| REQ-TEST-004 | Contract tests for agent I/O schemas | ENGINEERING | P0 | 1 | Invalid agent payloads rejected | Phase 3–4 | CI | Contract suite | planned |

---

## REQ-DEPLOY — Deployment / CI

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-DEPLOY-001 | CI foundation exists and fails correctly | ENGINEERING | P0 | 1 | GitHub Actions runs applicable checks; failures block merge conceptually | Phase 1 | CI | Workflow + run | documented |
| REQ-DEPLOY-002 | Do not add application linters/typecheckers before stack exists | ENGINEERING | P0 | 1 | CI only runs checks applicable to current repo contents | Phase 1 | Review | `docs/deployment/ci-cd.md` | documented |
| REQ-DEPLOY-003 | Deployment remains simple for Part 1 demo (single-env acceptable) | ENGINEERING | P1 | 1 | Deploy docs describe a minimal runnable path | Phase 7 | Smoke | Deploy doc | planned |
| REQ-DEPLOY-004 | Eventual CI enforces format/lint/types/tests/build/docs consistency | ENGINEERING | P1 | 1 | Roadmap tracks progressive CI enablement | Phase 1→7 | CI growth | Roadmap + workflows | documented |

---

## REQ-DOC — Documentation

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-DOC-001 | Technical documentation covers requirements, architecture, agents, ops | ASSIGNMENT | P0 | 1 | `docs/` structure populated for Phase 1 topics | Phase 1 | Docs check script | `docs/` tree | documented |
| REQ-DOC-002 | AI agents must follow `AGENTS.md` and update docs with behavior changes | ENGINEERING | P0 | 1 | `AGENTS.md` present; governance doc published | Phase 1 | Doc review | `AGENTS.md` | documented |
| REQ-DOC-003 | ADRs capture significant architecture decisions | ENGINEERING | P0 | Both | At least ADR-0001 for Phase 1 approach | Phase 1 | Doc review | `docs/decisions/` | documented |
| REQ-DOC-004 | Demo/submission instructions documented when implementation exists | ASSIGNMENT | P1 | 1 | Submission runbook lists how to demo Part 1 | Phase 7 | Manual | Ops runbook | planned |

---

## REQ-SEC — Security

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-SEC-001 | `.env` ignored; `.env.example` allowed without secrets | ENGINEERING | P0 | 1 | `.gitignore` + secret pattern check | Phase 1 | Script + CI | `.gitignore`, CI | documented |
| REQ-SEC-002 | No API keys/credentials in source, docs, or tests | ENGINEERING | P0 | 1 | Secret pattern scan clean | Phase 1 | Script + CI | CI logs | documented |
| REQ-SEC-003 | Safe logging policy (no secrets; careful with document PII) | ENGINEERING | P0 | 1 | Policy documented; later code complies | Phase 1→5 | Review | `docs/security/baseline.md` | documented |
| REQ-SEC-004 | Document upload security (type/size/malware considerations) addressed in implementation phases | ENGINEERING | P1 | 1 | Deferred with explicit later phase ownership | Phase 3+ | Security review | Security backlog | deferred |
| REQ-SEC-005 | Dependency pinning strategy defined before app dependencies are added | ENGINEERING | P1 | 1 | Strategy documented; enforced when lockfiles appear | Phase 2 | Review | `docs/security/baseline.md` | documented |

---

## REQ-SUBMISSION — Demo / assignment delivery

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-SUBMISSION-001 | Repository demonstrates Part 1 end-to-end when implementation complete | ASSIGNMENT | P0 | 1 | Clean + messy samples produce documented outcomes | Phase 7 | Demo script | Demo recording/notes | planned |
| REQ-SUBMISSION-002 | Evaluation results for samples are reproducible and recorded | ASSIGNMENT | P0 | 1 | Eval report checked in or generated by documented command | Phase 5–7 | Eval | Eval artifacts | planned |
| REQ-SUBMISSION-003 | Failure handling demonstrated (bad input / low confidence / rule miss) | ASSIGNMENT | P0 | 1 | Demo includes at least one non-happy-path | Phase 7 | Demo | Demo notes | planned |

---

## REQ-PART2 — Forward compatibility (do not implement in Part 1)

| ID | Requirement | Source | Priority | Part | Acceptance criteria | Planned phase | Planned test | Evidence required | Status |
|----|-------------|--------|----------|------|---------------------|---------------|--------------|-------------------|--------|
| REQ-PART2-001 | Preserve extension point for email ingestion triggers | ASSIGNMENT | P2 | 2 | Architecture documents ingestion port; Part 1 does not hard-wire only UI upload forever | Phase 1–2 | Design review | Extension points doc | documented |
| REQ-PART2-002 | Preserve extension point for file/attachment ingestion | ASSIGNMENT | P2 | 2 | Ingestion interface allows multiple sources | Phase 1–2 | Design review | Extension points doc | documented |
| REQ-PART2-003 | Support multiple documents per shipment later | ASSIGNMENT | P2 | 2 | Data model 1:N ready | Phase 2–5 | Schema review | ERD | planned |
| REQ-PART2-004 | Cross-document consistency validation later | ASSIGNMENT | P2 | 2 | Validation stage can accept multi-doc context later | Phase 1–4 | Design review | Extension points doc | documented |
| REQ-PART2-005 | Draft reply generation later | ASSIGNMENT | P2 | 2 | Communication port defined; unused in Part 1 | Phase 1–2 | Design review | Extension points doc | documented |
| REQ-PART2-006 | Human approval workflow later | ASSIGNMENT | P2 | 2 | Decision records allow later approval state transitions | Phase 1–5 | Design review | Extension points doc | documented |
| REQ-PART2-007 | Outbound sending workflows later | ASSIGNMENT | P2 | 2 | Outbound adapter not required in Part 1; interface reserved | Phase 1–2 | Design review | Extension points doc | documented |

---

## Counts

| Category | Count |
|----------|-------|
| REQ-PROD | 4 |
| REQ-EXT | 6 |
| REQ-VAL | 6 |
| REQ-ROUTER | 5 |
| REQ-DATA | 4 |
| REQ-QUERY | 3 |
| REQ-UI | 3 |
| REQ-AI | 6 |
| REQ-OBS | 4 |
| REQ-TEST | 4 |
| REQ-DEPLOY | 4 |
| REQ-DOC | 4 |
| REQ-SEC | 5 |
| REQ-SUBMISSION | 3 |
| REQ-PART2 | 7 |
| **Total** | **68** |

Assignment-sourced vs engineering-sourced are labeled per row in the **Source** column.
