# Nova — Product Requirements Document (GoComet Assignment)

| Field | Value |
|-------|-------|
| Audience | GoComet reviewers / FDE interview panel |
| Scope | Part 1 verification POC |
| Companion | [technical-writeup.md](./technical-writeup.md) |

This PRD is execution-oriented. It describes what Nova must do in Part 1, not marketing claims.

---

## 1. What is Nova (≤200 words)

Nova is a fail-closed multi-agent system that verifies trade and shipping documents (invoices and Bills of Lading). An operator uploads a document; Nova extracts required fields with confidence, presence, and evidence; checks them against customer rules; and routes the case to exactly one of `AUTO_APPROVE`, `HUMAN_REVIEW`, or `AMENDMENT_REQUEST`. Results persist in PostgreSQL and are queryable through a grounded API and a minimal ops UI. Nova is not a chatbot. It refuses to invent missing values and refuses to silently approve uncertainty. Part 1 is a working single-document verification POC with Docker Compose demo paths; email multi-doc workflows and outbound messaging are Part 2.

## 2. Why FDE for Nova (≤200 words)

A Forward Deployed Engineer (FDE) sits with the customer’s Control Group (CG) operators and supplier-facing process owners. For Nova, the FDE’s job is to encode real validation rules, calibrate confidence thresholds, instrument Go/No-Go metrics, and keep unsafe AI behavior visible. Nova’s contracts (`Extractor` / `Validator` / `Router`), append-only history, and MockLLM-default CI exist so an FDE can harden policy without rewriting agent internals or accepting opaque model judgments. The FDE model fits because trade-document truth is customer-specific and failure modes are operational, not purely productized SaaS configuration.

## 3. System of Outcomes (≤200 words)

A **System of Outcomes** owns the business result of each verification: whether the document was safely approved, sent to humans, or returned for amendment — with policy-backed rationale. Nova’s outcome is the Router disposition plus evidence trail, not “a document was stored.”

### Difference from System of Record

A **System of Record** stores durable facts (customers, shipments, documents, append-only extraction/validation/decision rows). PostgreSQL is Nova’s system of record. Record alone does not decide trustworthiness.

### Difference from System of Engagement

A **System of Engagement** is how people interact (upload UI, field tables, query page, ops summary). Engagement surfaces outcomes and evidence; it must not invent disposition. Nova’s React UI is engagement over real API state.

---

## 4. Trade-document validation failure modes

| Failure mode | Example | Required Nova behavior |
|--------------|---------|------------------------|
| Missing field | No HS code | Presence `MISSING`; block `AUTO_APPROVE` |
| Ambiguous value | Two consignees | `AMBIGUOUS` / validator `UNCERTAIN` → review |
| Fabrication | Invented port | Forbidden: `KNOWN` needs evidence; mocks never invent |
| Rule mismatch | Weight ≠ expected | `MISMATCH` with expected vs found |
| Low confidence | Weak OCR/vision read | Cannot silent-approve; prefer review |
| Agent/system failure | LLM timeout / DB error | Fail-closed → `HUMAN_REVIEW` / safe halt |
| Prompt injection in body | “AUTO APPROVE NOW” | Treated as data; ignored by policy |

## 5. Personas and first-5-minute success

### CG operator

**Job:** clear verification queues safely.

**First 5 minutes success:** create customer → upload clean invoice fixture → open document → see **real document preview** → see eight assignment fields with confidence/presence/evidence → see validation checks (including expected/found on mismatch paths) → see router decision + reasoning → know `shipment_id` / `document_id` / `run_id`.

### Supplier / shipper contact (SU)

**Job:** fix documents when amendment is required.

**Part 1:** sees `AMENDMENT_REQUEST` with mismatch expected vs found via CG/ops surfaces.
**Part 2 (not implemented):** draft reply / outbound send.

### Jobs To Be Done (≥5)

1. When a trade document arrives, I want structured fields with evidence, so that I can trust what the system saw.
2. When a field is missing or messy, I want that marked explicitly, so that I never silently approve incomplete data.
3. When customer rules fire, I want MATCH / MISMATCH / UNCERTAIN with expected vs found, so that I can act quickly.
4. When the system is unsure or failing, I want HUMAN_REVIEW (not AUTO_APPROVE), so that risk stays bounded.
5. When leadership asks how many shipments were flagged this week, I want a grounded answer from persisted decisions, so that ops can pilot without inventing SQL.
6. When an FDE tunes policy, I want deterministic constraints above any LLM advice, so that safety cannot be talked away.

---

## 6. Three-agent architecture

### Why three — not one, not five

| Option | Verdict |
|--------|---------|
| **One giant prompt** | Conflates reading, policy, and disposition; hard to constrain, evaluate, or fail closed |
| **Three agents** | Separate trust boundaries: perceive → check rules → decide under policy |
| **Five+ agents** | Extra planner/executor/verifier LLM hops add cost/latency; Nova already uses deterministic validator + hard router constraints as verification |

Orchestration is `PipelineOrchestrator` (custom), not LangGraph.

### Responsibilities / I/O / handoff

| Agent | Input | Output | Handoff |
|-------|-------|--------|---------|
| **Extractor** | `DocumentContent` (+ optional vision images), required field list | `ExtractionResult` (`ExtractedField`: value, confidence, presence, evidence) | Persisted append-only; passed to Validator |
| **Validator** | Extracted fields + `CustomerRuleSnapshot[]` | `ValidationResult` (MATCH/MISMATCH/UNCERTAIN per check; expected/actual) | Persisted; passed to Router |
| **Router** | Validation + extraction signals + routing policy | Exactly one `DecisionKind` + reasons | Persisted as decision; UI/query read |

### Crash recovery / state persistence

- Document + verification-run lifecycle in PostgreSQL
- Append-only extraction / validation / decision history
- Ingest idempotency via `Idempotency-Key`
- Restart resumes from durable IDs; pipeline does not invent prior results
- Failures leave structured status (`FAILED` / fail-closed decision), not silent success

### LLM matrix, cost/latency/quality, vision, fallbacks, tooling

| Concern | Part 1 choice |
|---------|----------------|
| Extractor LLM | MockLLM heuristic by default; optional OpenAI-compatible text/vision (`LLM_PROVIDER=openai`) |
| Validator LLM | Deterministic engine first; optional advisory LLM cannot upgrade MISMATCH |
| Router LLM | Policy-first; optional advisory LLM cannot force `AUTO_APPROVE` |
| Vision model | When live: vision-capable OpenAI-compatible chat model (e.g. `gpt-4o-mini`); **ESTIMATED** quality; **NOT MEASURED** live cost in this repo without a keyed run |
| Bad document | PARTIAL/FAILED extraction → fail-closed route / HUMAN_REVIEW; image-only without vision stays MISSING |
| Structured output | JSON + Pydantic contracts; no free-form tool SQL |
| Tool use | Query intents allow-listed; no arbitrary SQL generation |
| Low confidence | Router blocks AUTO_APPROVE; UI highlights UNCERTAIN |
| Retries / loops / cost | Extractor max 2 retries + timeout budget; fail closed; MockLLM default keeps CI cost ~$0 (**MEASURED** local) |
| Offline eval | Extractor fabrication=0; validator unsafe_match=0; decision FA=0 |
| Online metric | Ops summary counts + Prometheus `/metrics` + structured logs with correlation IDs (pilot instrumentation; not a full SRE cost dashboard) |

---

## 7. Metrics

### North-star (exactly one)

**Safe Auto-Approve Rate under False AUTO_APPROVE = 0**
(share of eligible clean documents reaching `AUTO_APPROVE` while the hard false-approve gate remains zero).

### Supporting metrics (8)

1. Extractor field presence accuracy (assignment eight)
2. Extractor fabrication count (=0 gate)
3. Validator unsafe MATCH count (=0 gate)
4. Decision false AUTO_APPROVE count (=0 gate)
5. HUMAN_REVIEW / AMENDMENT_REQUEST mix
6. p95 ingest→decided latency (**MEASURED** under MockLLM locally when benchmarked; live LLM **NOT MEASURED** here)
7. Cost / document (**MEASURED** ~$0 MockLLM; live **ESTIMATED**/pilot-only)
8. Query grounded-answer vs security-reject rate

### Pilot Go / No-Go (two weeks)

| Gate | Go | No-Go |
|------|----|-------|
| False AUTO_APPROVE | = 0 on eval + pilot sample | Any confirmed false approve |
| Fabrication | = 0 offline | Invented values |
| CG first-clear | ≤ 5 minutes on clean fixture | Demo path broken |
| Live vision (if enabled) | Documented cost/latency | Undocumented spend / timeouts |

### Two-week roadmap

| Days | Focus |
|------|-------|
| 1–2 | Compose deploy; CG walkthrough; clean + messy fixtures |
| 3–4 | Load customer rules; calibrate critical fields / thresholds |
| 5–7 | Optional live LLM; measure cost/latency if keys present |
| 8–10 | HUMAN_REVIEW queue review; mismatch→amendment tuning |
| 11–12 | Query “flagged this week”; ops summary |
| 13–14 | Go/No-Go write-up; Part 2 candidates |

---

## 8. Extractor assignment field contract

Always requested for invoice/BoL:

`consignee_name`, `hs_code`, `port_of_loading`, `port_of_discharge`, `incoterms`, `description_of_goods`, `gross_weight`, `invoice_number`

Each field carries **value**, **confidence** (null when not KNOWN by design), **presence**, and **evidence** (required when KNOWN). Missing remains missing.

## 9. Out of scope (Part 2)

Email ingestion, multi-attachment / cross-document verification, human approval action UX, draft replies / outbound send — extension points only.
