# Functional requirements

Stable requirement cards for Nova behavior. Do not renumber; deprecate and replace if needed.

## Legend

| Field | Allowed values |
|-------|----------------|
| **Source** | `ASSIGNMENT REQUIREMENT` · `ENGINEERING REQUIREMENT` |
| **Priority** | `P0` must for Part 1 · `P1` should for Part 1 · `P2` Part 2 / later |
| **Scope** | `Part 1` · `Part 2` · `Both` |
| **Status** | `documented` · `planned` · `in_progress` · `done` · `deferred` |

**Implementation phases (planned):**

| Phase | Focus |
|-------|-------|
| 1 | Foundation (requirements, docs, CI, governance) |
| 2 | Contracts, principles, Part 2 extension points |
| 3 | Ingestion + extraction |
| 4 | Validation + routing |
| 5 | Persistence + sample evaluation harness |
| 6 | Query layer + minimal UI |
| 7 | Demo / submission polish |
| Part 2 | Deferred product features (not Part 1 implementation) |

---

## REQ-PROD — Product framing

### REQ-PROD-001

| Field | Value |
|-------|-------|
| **ID** | REQ-PROD-001 |
| **Description** | Nova verifies trade/shipping documents (for example invoices and Bills of Lading) as an **operational verification system**, not as a generic chat product. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Product docs and eventual demo describe operational verification workflow (ingest → extract → validate → route → persist → query/UI). |
| **Implementation phase** | 1 (docs); demonstrated in 7 |
| **Test strategy** | Documentation review; demo script review |
| **Evidence** | `docs/product/nova.md`, `docs/product/problem-statement.md`, demo notes |
| **Status** | documented |

### REQ-PROD-002

| Field | Value |
|-------|-------|
| **ID** | REQ-PROD-002 |
| **Description** | Nova addresses the expensive, error-prone manual email verification loop between shipper and validation team. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Problem statement documents manual workflow, pain points, and desired operational outcome. |
| **Implementation phase** | 1 |
| **Test strategy** | Documentation review |
| **Evidence** | `docs/product/problem-statement.md` |
| **Status** | documented |

### REQ-PROD-003

| Field | Value |
|-------|-------|
| **ID** | REQ-PROD-003 |
| **Description** | The system must not auto-approve blindly when confidence, evidence, or rules indicate risk. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Router can emit `HUMAN_REVIEW` and `AMENDMENT_REQUEST`; policy forbids silent auto-approve on uncertainty or failure. |
| **Implementation phase** | 2 (policy design) → 4 (implementation) |
| **Test strategy** | Design review; golden routing cases; failure tests |
| **Evidence** | Router policy docs; golden fixtures; failure-test results |
| **Status** | documented |

### REQ-PROD-004

| Field | Value |
|-------|-------|
| **ID** | REQ-PROD-004 |
| **Description** | Human review remains a first-class path for uncertain or high-risk cases. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Both |
| **Acceptance criteria** | `HUMAN_REVIEW` is a documented router decision; Part 2 may add approval UX without redesigning the decision enum. |
| **Implementation phase** | 4 (decision); Part 2 (approval actions) |
| **Test strategy** | Design review; router golden cases |
| **Evidence** | Router contract; scope docs; Part 2 extension points |
| **Status** | documented |

---

## REQ-EXT — Document input and extraction

### REQ-EXT-001

| Field | Value |
|-------|-------|
| **ID** | REQ-EXT-001 |
| **Description** | Accept trade/shipping document input into the Part 1 pipeline (file/path or upload abstraction). |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | An operator or API client can submit a supported document and obtain a verification run identifier. |
| **Implementation phase** | 3 |
| **Test strategy** | Integration test with fixture document |
| **Evidence** | Ingestion contract; API/demo run log |
| **Status** | planned |

### REQ-EXT-002

| Field | Value |
|-------|-------|
| **ID** | REQ-EXT-002 |
| **Description** | An Extractor Agent extracts the **required business fields** for the supported document type. Exact field schemas are defined from sample documents and customer rules during implementation — not invented here. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Typed extraction output returns the required field set for each supported Part 1 document type used in samples. |
| **Implementation phase** | 3 |
| **Test strategy** | Unit/contract tests; golden extraction on clean sample |
| **Evidence** | Extraction schema; sample extraction outputs |
| **Status** | planned |

### REQ-EXT-003

| Field | Value |
|-------|-------|
| **ID** | REQ-EXT-003 |
| **Description** | Each extracted field includes a confidence score (or an explicit null/absent confidence with a recorded reason). |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Extraction schema mandates confidence metadata per field; low confidence is visible downstream. |
| **Implementation phase** | 3 |
| **Test strategy** | Schema/contract tests; evaluation on messy sample |
| **Evidence** | Schema definition; eval report |
| **Status** | planned |

### REQ-EXT-004

| Field | Value |
|-------|-------|
| **ID** | REQ-EXT-004 |
| **Description** | Each extracted field includes evidence/grounding sufficient for audit and human review (for example snippet or page/region reference). |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Reviewer can locate why a field value was proposed from the stored evidence reference. |
| **Implementation phase** | 3 |
| **Test strategy** | Contract tests; manual review checklist on samples |
| **Evidence** | Sample runs with evidence payloads; UI/API screenshots |
| **Status** | planned |

### REQ-EXT-005

| Field | Value |
|-------|-------|
| **ID** | REQ-EXT-005 |
| **Description** | Provide at least one **clean** sample document and one **messy/hard** sample, used in evaluation. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Both samples are checked in (or clearly licensed fixtures) and exercised by the evaluation harness. |
| **Implementation phase** | 5 |
| **Test strategy** | Eval harness run in CI or documented command |
| **Evidence** | `fixtures/` (or equivalent); eval artifacts |
| **Status** | planned |

### REQ-EXT-006

| Field | Value |
|-------|-------|
| **ID** | REQ-EXT-006 |
| **Description** | Extraction failures are isolated and reported without crashing the service; downstream disposition remains fail-safe. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Failed extraction yields a structured error and/or `UNCERTAIN` path; no silent `AUTO_APPROVE`. |
| **Implementation phase** | 3–4 |
| **Test strategy** | Failure/chaos tests (corrupt input, timeout) |
| **Evidence** | Failure-test results; structured error examples |
| **Status** | planned |

---

## REQ-VAL — Validation

### REQ-VAL-001

| Field | Value |
|-------|-------|
| **ID** | REQ-VAL-001 |
| **Description** | Validate extracted fields against **customer-specific rules**. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | A per-customer rule set can be applied to an extraction result and produce structured outcomes. |
| **Implementation phase** | 4 |
| **Test strategy** | Unit tests with fixture rule packs |
| **Evidence** | Rules format doc; fixture tests |
| **Status** | planned |

### REQ-VAL-002

| Field | Value |
|-------|-------|
| **ID** | REQ-VAL-002 |
| **Description** | Produce validation result **MATCH** when rules are satisfied within policy. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Golden case emits `MATCH` with identifiable rule IDs. |
| **Implementation phase** | 4 |
| **Test strategy** | Golden / unit tests |
| **Evidence** | Golden fixtures + CI results |
| **Status** | planned |

### REQ-VAL-003

| Field | Value |
|-------|-------|
| **ID** | REQ-VAL-003 |
| **Description** | Produce validation result **MISMATCH** when rules are violated, with field-level reasons. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Golden case emits `MISMATCH` with reasons suitable for amendment or review. |
| **Implementation phase** | 4 |
| **Test strategy** | Golden / unit tests |
| **Evidence** | Golden fixtures + CI results |
| **Status** | planned |

### REQ-VAL-004

| Field | Value |
|-------|-------|
| **ID** | REQ-VAL-004 |
| **Description** | Produce validation result **UNCERTAIN** when confidence, evidence, or rules are insufficient to decide. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Golden case emits `UNCERTAIN` rather than forcing MATCH/MISMATCH. |
| **Implementation phase** | 4 |
| **Test strategy** | Golden / unit tests |
| **Evidence** | Golden fixtures + CI results |
| **Status** | planned |

### REQ-VAL-005

| Field | Value |
|-------|-------|
| **ID** | REQ-VAL-005 |
| **Description** | Prefer deterministic validation for clear rule checks; use LLM reasoning only where judgment is genuinely required, with an explicit boundary. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Design documents which checks are deterministic vs LLM-assisted; deterministic checks are unit-tested without network. |
| **Implementation phase** | 2–4 |
| **Test strategy** | Design review; unit tests for deterministic path |
| **Evidence** | Validator design/ADR; unit suite |
| **Status** | planned |

### REQ-VAL-006

| Field | Value |
|-------|-------|
| **ID** | REQ-VAL-006 |
| **Description** | Validation output is auditable: inputs, rule identifiers, and outcomes can reconstruct why a result was produced. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Persisted validation record includes enough metadata to explain MATCH/MISMATCH/UNCERTAIN. |
| **Implementation phase** | 4–5 |
| **Test strategy** | Integration test reading persisted audit fields |
| **Evidence** | Schema/API examples; integration test |
| **Status** | planned |

---

## REQ-ROUTER — Routing decisions

### REQ-ROUTER-001

| Field | Value |
|-------|-------|
| **ID** | REQ-ROUTER-001 |
| **Description** | Router Agent can decide **AUTO_APPROVE** when policy thresholds are met. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Golden case produces `AUTO_APPROVE` only under documented policy. |
| **Implementation phase** | 4 |
| **Test strategy** | Golden / policy unit tests |
| **Evidence** | Router policy + fixtures |
| **Status** | planned |

### REQ-ROUTER-002

| Field | Value |
|-------|-------|
| **ID** | REQ-ROUTER-002 |
| **Description** | Router Agent can decide **HUMAN_REVIEW** for uncertain or high-risk cases. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Golden case produces `HUMAN_REVIEW` for low confidence / UNCERTAIN / policy risk. |
| **Implementation phase** | 4 |
| **Test strategy** | Golden / policy unit tests |
| **Evidence** | Router policy + fixtures |
| **Status** | planned |

### REQ-ROUTER-003

| Field | Value |
|-------|-------|
| **ID** | REQ-ROUTER-003 |
| **Description** | Router Agent can decide **AMENDMENT_REQUEST** when the shipper must correct or resubmit. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Golden case produces `AMENDMENT_REQUEST` for clear MISMATCH patterns defined by policy. |
| **Implementation phase** | 4 |
| **Test strategy** | Golden / policy unit tests |
| **Evidence** | Router policy + fixtures |
| **Status** | planned |

### REQ-ROUTER-004

| Field | Value |
|-------|-------|
| **ID** | REQ-ROUTER-004 |
| **Description** | Routing policy is explicit and reviewable — not opaque prompt-only behavior. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Thresholds/conditions are documented and testable; LLM may assist but cannot be the sole untestable authority. |
| **Implementation phase** | 2–4 |
| **Test strategy** | Design review; policy unit tests |
| **Evidence** | `docs/agents/` (or equivalent) router policy |
| **Status** | planned |

### REQ-ROUTER-005

| Field | Value |
|-------|-------|
| **ID** | REQ-ROUTER-005 |
| **Description** | On tool/LLM failure, the router must not silently upgrade risk to `AUTO_APPROVE`. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Failure fixtures default to `HUMAN_REVIEW` or a safe halt state. |
| **Implementation phase** | 4 |
| **Test strategy** | Failure tests |
| **Evidence** | Failure fixtures + results |
| **Status** | planned |

---

## REQ-DATA — Persistence

### REQ-DATA-001

| Field | Value |
|-------|-------|
| **ID** | REQ-DATA-001 |
| **Description** | Persist shipment, document, validation, and decision information. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | After a run, records for shipment/document/validation/decision are retrievable. |
| **Implementation phase** | 5 |
| **Test strategy** | Integration tests |
| **Evidence** | Schema + API responses |
| **Status** | planned |

### REQ-DATA-002

| Field | Value |
|-------|-------|
| **ID** | REQ-DATA-002 |
| **Description** | Data model allows multiple documents per shipment (Part 1 may process one) so Part 2 multi-attachment does not require a breaking redesign. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Both |
| **Acceptance criteria** | Schema/ERD shows 1:N shipment→document without breaking Part 1 single-doc flows. |
| **Implementation phase** | 2–5 |
| **Test strategy** | Schema review; migration tests when present |
| **Evidence** | ERD / database docs |
| **Status** | planned |

### REQ-DATA-003

| Field | Value |
|-------|-------|
| **ID** | REQ-DATA-003 |
| **Description** | Writes are idempotent where re-processing the same document is possible. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P1 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Re-submit with the same idempotency key does not create unbounded duplicate runs/records. |
| **Implementation phase** | 5 |
| **Test strategy** | Integration tests |
| **Evidence** | Idempotency tests |
| **Status** | planned |

---

## REQ-QUERY — Query layer

### REQ-QUERY-001

| Field | Value |
|-------|-------|
| **ID** | REQ-QUERY-001 |
| **Description** | Provide a query layer over persisted verification data. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Operators can retrieve shipments, documents, validations, and decisions programmatically. |
| **Implementation phase** | 5–6 |
| **Test strategy** | Integration tests |
| **Evidence** | API examples; integration results |
| **Status** | planned |

### REQ-QUERY-002

| Field | Value |
|-------|-------|
| **ID** | REQ-QUERY-002 |
| **Description** | Support **natural-language query** over persisted verification data. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Example NL questions return answers grounded in stored records for demo/eval cases. |
| **Implementation phase** | 6 |
| **Test strategy** | Integration + evaluation cases |
| **Evidence** | Query examples; traces |
| **Status** | planned |

### REQ-QUERY-003

| Field | Value |
|-------|-------|
| **ID** | REQ-QUERY-003 |
| **Description** | Natural-language query must not invent facts absent from persisted data. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Answers cite records or explicitly refuse when unknown; adversarial eval cases pass. |
| **Implementation phase** | 6 |
| **Test strategy** | Adversarial eval suite |
| **Evidence** | Eval cases + results |
| **Status** | planned |

---

## REQ-UI — Operations UI

### REQ-UI-001

| Field | Value |
|-------|-------|
| **ID** | REQ-UI-001 |
| **Description** | Provide a **minimal B2B operations UI** for core verification operations. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | UI supports submit/view documents and view extraction, validation, and decision outcomes. |
| **Implementation phase** | 6 |
| **Test strategy** | Smoke tests; manual demo checklist |
| **Evidence** | Screenshots; demo recording/notes |
| **Status** | planned |

### REQ-UI-002

| Field | Value |
|-------|-------|
| **ID** | REQ-UI-002 |
| **Description** | UI surfaces confidence, evidence, and validation outcomes so a reviewer can understand a decision. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Review checklist confirms confidence, evidence, and validation are visible on a detail view. |
| **Implementation phase** | 6 |
| **Test strategy** | Manual UI checklist |
| **Evidence** | Checklist + screenshots |
| **Status** | planned |

### REQ-UI-003

| Field | Value |
|-------|-------|
| **ID** | REQ-UI-003 |
| **Description** | UI remains usable for reading a `HUMAN_REVIEW` queue even if approval *actions* are deferred to Part 2. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P1 |
| **Scope** | Both |
| **Acceptance criteria** | Review list/detail is readable in Part 1 without implementing outbound approval workflows. |
| **Implementation phase** | 6 |
| **Test strategy** | Manual UI checklist |
| **Evidence** | Screenshots; scope note |
| **Status** | planned |

---

## REQ-AI — Agents / LLM usage

### REQ-AI-001

| Field | Value |
|-------|-------|
| **ID** | REQ-AI-001 |
| **Description** | Use a distinct **Extractor Agent** with a typed input/output contract. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Extractor is separable from validator/router; I/O schema is documented and contract-tested. |
| **Implementation phase** | 3 |
| **Test strategy** | Contract tests |
| **Evidence** | Agent docs; contract suite |
| **Status** | planned |

### REQ-AI-002

| Field | Value |
|-------|-------|
| **ID** | REQ-AI-002 |
| **Description** | Use a distinct **validation stage** (deterministic engine and/or validator agent) with a typed contract. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Validation stage is separable and contract-tested; emits MATCH/MISMATCH/UNCERTAIN. |
| **Implementation phase** | 4 |
| **Test strategy** | Contract + golden tests |
| **Evidence** | Agent/validator docs; test report |
| **Status** | planned |

### REQ-AI-003

| Field | Value |
|-------|-------|
| **ID** | REQ-AI-003 |
| **Description** | Use a distinct **Router Agent** that emits the typed decision enum. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Router I/O is typed to `AUTO_APPROVE` \| `HUMAN_REVIEW` \| `AMENDMENT_REQUEST`. |
| **Implementation phase** | 4 |
| **Test strategy** | Contract + golden tests |
| **Evidence** | Agent docs; test report |
| **Status** | planned |

### REQ-AI-004

| Field | Value |
|-------|-------|
| **ID** | REQ-AI-004 |
| **Description** | Extraction/validation must be confidence-aware; fields must not be presented as certain when hallucinated or ungounded. |
| **Source** | ENGINEERING REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Missing/low-confidence fields are flagged; eval shows no silent high-confidence inventions on messy sample beyond policy. |
| **Implementation phase** | 3–4 |
| **Test strategy** | Evaluation harness |
| **Evidence** | Eval report |
| **Status** | planned |

---

## REQ-SUBMISSION — Demo / assignment delivery

### REQ-SUBMISSION-001

| Field | Value |
|-------|-------|
| **ID** | REQ-SUBMISSION-001 |
| **Description** | Repository demonstrates Part 1 end-to-end when implementation is complete. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Clean and messy samples produce documented pipeline outcomes. |
| **Implementation phase** | 7 |
| **Test strategy** | Demo script |
| **Evidence** | Demo notes/recording |
| **Status** | planned |

### REQ-SUBMISSION-002

| Field | Value |
|-------|-------|
| **ID** | REQ-SUBMISSION-002 |
| **Description** | Evaluation results for samples are reproducible and recorded. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Eval report is checked in or generated by a documented command. |
| **Implementation phase** | 5–7 |
| **Test strategy** | Eval command reproducibility |
| **Evidence** | Eval artifacts |
| **Status** | planned |

### REQ-SUBMISSION-003

| Field | Value |
|-------|-------|
| **ID** | REQ-SUBMISSION-003 |
| **Description** | Failure handling is demonstrated (bad input, low confidence, and/or rule miss). |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P0 |
| **Scope** | Part 1 |
| **Acceptance criteria** | Demo includes at least one non-happy-path with expected safe disposition. |
| **Implementation phase** | 7 |
| **Test strategy** | Demo script |
| **Evidence** | Demo notes |
| **Status** | planned |

---

## Counts (functional)

| Category | Count |
|----------|-------|
| REQ-PROD | 4 |
| REQ-EXT | 6 |
| REQ-VAL | 6 |
| REQ-ROUTER | 5 |
| REQ-DATA | 3 |
| REQ-QUERY | 3 |
| REQ-UI | 3 |
| REQ-AI | 4 |
| REQ-SUBMISSION | 3 |
| **Total (this file)** | **37** |

Non-functional, security, test, deploy, doc, observability, remaining AI, data, and Part 2 requirements are in sibling documents.
