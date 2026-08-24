# Solution definition (conceptual)

Nova is an operational pipeline. Agents are components inside that pipeline — not the product definition by themselves.

```text
Document
  → ingestion
  → extraction
  → confidence / evidence
  → validation
  → routing
  → persistence
  → query
  → UI
```

No stage is implemented in Phase 1; this document defines intent for later phases.

---

## Ingestion

Accept a document into a verification **run** bound to a **shipment** (or create shipment + document).

Part 1: simple upload/path input is enough.  
Part 2-ready: ingestion is a port so email and multi-attachment sources can plug in later.

Outputs: stored document reference, content handle, run ID.

## Extraction

Extractor Agent reads the document and returns required business fields for the document type.

Outputs: typed field map.

## Confidence / evidence

For each field:

- **Confidence** — how certain the system is in the value
- **Evidence** — grounding pointer (snippet, page/region reference, or equivalent)

Low confidence must flow downstream; it is not cosmetic.

## Validation

Compare extracted fields to **customer-specific rules**.

Prefer deterministic evaluation for crisp checks (equality, required presence, numeric tolerances, allow-lists). Use LLM reasoning only where judgment is genuinely needed, and keep that boundary explicit.

Outputs per field/rule: **MATCH**, **MISMATCH**, or **UNCERTAIN**, with reasons.

## Routing

Router Agent (policy + reasoning as designed) chooses disposition:

| Decision | Meaning |
|----------|---------|
| `AUTO_APPROVE` | Safe to proceed without human touch under policy |
| `HUMAN_REVIEW` | Analyst must review before proceeding |
| `AMENDMENT_REQUEST` | Shipper should correct/resubmit |

Fail-safe: errors and policy misses must not become silent auto-approvals.

## Persistence

Store shipment, document(s), extraction results, validation results, and routing decisions with enough metadata for audit and replay (model/prompt versions where applicable).

## Query

Provide programmatic retrieval and a **natural-language query** layer over persisted data. Answers must be grounded in stored records or explicitly refuse.

## UI

Minimal B2B operations interface: submit/view documents, inspect fields/confidence/evidence, see validation and routing outcomes, support review-oriented reading of HUMAN_REVIEW cases.

---

## Design stance

- Typed contracts between stages
- Observability per run
- Part 2 extension points without implementing Part 2
- Production failure handling (timeouts, retries with limits, isolation)
