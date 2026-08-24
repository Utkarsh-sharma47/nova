# Nova domain model

Logical domain model for Nova’s system of record. This document defines **entities and invariants**, not application code, repositories, or agent implementations.

**Persistence technology:** PostgreSQL ([ADR-0003](../decisions/0003-database.md)).  
**Physical schema:** [schema-design.md](./schema-design.md).  
**Relationships:** [relationships.md](./relationships.md).  
**Audit:** [audit-model.md](./audit-model.md).

---

## Data classification

Every persisted attribute belongs to exactly one primary class (a field may *also* be referenced in audit events):

| Class | Meaning | Mutability | Examples |
|-------|---------|------------|----------|
| **Business data** | Facts about customers, shipments, documents, and configured rules | Mutable under controlled workflows; versioned where history matters | Customer name, shipment reference, document type, rule expressions |
| **AI-generated data** | Structured outputs produced by Extractor / Validator (LLM path) / Router | **Append-only** after a successful stage write; corrections create new versions/runs | Extracted values, confidence, evidence, LLM check reasons, decision reasoning, model/prompt metadata |
| **Derived data** | Values computed from business + AI inputs by deterministic policy | Recomputable; may be denormalized for query | Aggregate validation status, “current” document version pointer, rollup mismatch counts |
| **Audit data** | Immutable trail of who/what/when for security and reconstructability | **Append-only forever** (retention policy may archive, not rewrite) | `AuditEvent` rows, decision history snapshots |

**Rules**

- Do not store *only* free-form LLM prose as the system of record. Structured fields must remain queryable; free-text is optional commentary beside typed columns/JSON.
- Never silently convert `UNCERTAIN` / low confidence into `AUTO_APPROVE` in stored state.
- Part 1 may create one document per shipment; the model **must** allow many documents per shipment for Part 2 cross-document validation.

---

## Entity catalog

### 1. Customer

| Aspect | Definition |
|--------|------------|
| **Purpose** | Account / consignee / shipper-policy owner whose documents Nova verifies and whose rules apply. |
| **Lifecycle** | `draft` → `active` → `suspended` → `archived`. Soft-deleted customers cannot start new shipments; historical data remains readable for audit. |
| **Identity** | `customer_id` (UUID). Optional `external_key` unique when present (ERP/CRM id). |
| **Required fields** | `customer_id`, `name`, `status`, `created_at`, `updated_at` |
| **Optional fields** | `external_key`, `default_timezone`, `metadata` (JSON, non-secret), `archived_at`, `deleted_at` |
| **Relationships** | 1 → N `Shipment`; 1 → N `CustomerRule`; referenced by audit subjects |
| **Invariants** | `name` non-empty; `status` in allowed enum; soft-deleted customers have `deleted_at` set and `status = archived` |
| **Audit** | Create/update/archive/rule-bind emit `AuditEvent` with actor + before/after summary |
| **Class** | Business data |

---

### 2. Shipment

| Aspect | Definition |
|--------|------------|
| **Purpose** | Unit of operational verification work for a trade movement. Owns the document set and the verification timeline. |
| **Lifecycle** | `open` → `ingesting` → `extracting` → `validating` → `routing` → `decided` → `closed`. Amendment / resubmit may return to `ingesting` without erasing prior runs. |
| **Identity** | `shipment_id` (UUID). Within a customer, `customer_shipment_ref` unique when provided. |
| **Required fields** | `shipment_id`, `customer_id`, `status`, `created_at`, `updated_at` |
| **Optional fields** | `customer_shipment_ref`, `priority`, `closed_at`, `metadata` |
| **Relationships** | N → 1 `Customer`; 1 → N `Document`; 1 → N `VerificationRun` (supporting); 1 → N `Validation`; 1 → N `Decision` |
| **Invariants** | Always belongs to exactly one customer; status transitions are monotonic except documented reopen-for-amendment; deletion of shipment with decisions is soft or blocked |
| **Audit** | Status transitions and ownership changes audited |
| **Class** | Business data (+ derived `status` from pipeline progress) |

**Part 2 note:** Shipment is the anchor for multi-document packets and future email-thread correlation—not a single blob row.

---

### 3. Document

| Aspect | Definition |
|--------|------------|
| **Purpose** | One logical document in a shipment (invoice, Bill of Lading, packing list, etc.). Content lives on versions. |
| **Lifecycle** | `registered` → `content_available` → `in_pipeline` → `extracted` → `superseded` / `withdrawn`. |
| **Identity** | `document_id` (UUID). |
| **Required fields** | `document_id`, `shipment_id`, `document_type`, `status`, `created_at`, `updated_at` |
| **Optional fields** | `display_name`, `source_system`, `ingestion_channel` (`upload` \| `path` \| `email` \| `api` — Part 1 uses upload/path), `content_fingerprint` (latest), `current_version_id`, `deleted_at` |
| **Relationships** | N → 1 `Shipment`; 1 → N `DocumentVersion`; extraction fields hang off versions/runs |
| **Invariants** | `document_type` from controlled vocabulary; `current_version_id` null or points to a version of **this** document; shipment may have many documents of mixed types; duplicate **content** for same shipment+type is controlled via idempotency (see schema) |
| **Audit** | Register, replace content, withdraw audited |
| **Class** | Business data |

---

### 4. DocumentVersion

| Aspect | Definition |
|--------|------------|
| **Purpose** | Immutable snapshot of document bytes + storage locator. Amendments and resubmits create new versions; they do not overwrite prior bytes. |
| **Lifecycle** | `created` (terminal for content). Marked current via `Document.current_version_id`. |
| **Identity** | `document_version_id` (UUID). Unique `(document_id, version_number)`. |
| **Required fields** | `document_version_id`, `document_id`, `version_number`, `storage_uri`, `content_sha256`, `media_type`, `byte_size`, `created_at` |
| **Optional fields** | `original_filename`, `page_count`, `ingestion_idempotency_key`, `source_message_id` (Part 2 email), `created_by` |
| **Relationships** | N → 1 `Document`; 1 → N extraction outputs (via run); referenced by evidence pointers |
| **Invariants** | `version_number` ≥ 1 and contiguous per document; `content_sha256` length/format valid; rows are never updated except rare admin quarantine flags (prefer new row); storage URI contains no credentials |
| **Audit** | Creation audited; content itself is not duplicated into audit tables |
| **Class** | Business data (blob is sensitive; store by reference) |

---

### 5. ExtractedField

| Aspect | Definition |
|--------|------------|
| **Purpose** | One typed business field extracted from a specific document version during a verification run. |
| **Lifecycle** | Created when extraction stage succeeds for that field (or records explicit absence). Immutable thereafter; re-extraction creates new rows under a new run. |
| **Identity** | `extracted_field_id` (UUID). Unique `(verification_run_id, document_version_id, field_key)`. |
| **Required fields** | `extracted_field_id`, `verification_run_id`, `document_version_id`, `field_key`, `value_json`, `value_type`, `confidence`, `evidence_json`, `created_at` |
| **Optional fields** | `normalized_value_json`, `is_missing`, `absence_reason`, `extractor_notes` (short text), `model_call_id` (FK to model metadata) |
| **Relationships** | N → 1 document version; N → 1 verification run; consumed by `ValidationCheck` |
| **Invariants** | `confidence` in `[0, 1]` or null **only** with `absence_reason`; `evidence_json` is structured (page/region/snippet refs)—empty evidence requires explicit flag; `is_missing = true` ⇒ value null/empty and must not be treated as certain; never invent values marked high-confidence without evidence |
| **Audit** | Stage completion audited at run level; field payloads queryable without parsing logs |
| **Class** | **AI-generated data** (normalized copy may be derived) |

**`evidence_json` shape (logical):**

```json
{
  "kind": "bbox" | "text_span" | "page_text" | "none",
  "page": 1,
  "bbox": {"x": 0, "y": 0, "w": 0, "h": 0},
  "snippet": "…",
  "char_start": 0,
  "char_end": 0
}
```

---

### 6. CustomerRule

| Aspect | Definition |
|--------|------------|
| **Purpose** | Versioned, customer-specific validation rule used by the Validator stage. |
| **Lifecycle** | `draft` → `active` → `retired`. New versions supersede prior active rules with same `rule_key` (effective dating). |
| **Identity** | `customer_rule_id` (UUID). Unique active `(customer_id, rule_key)` where `status = active`. |
| **Required fields** | `customer_rule_id`, `customer_id`, `rule_key`, `rule_version`, `status`, `check_kind`, `severity`, `definition_json`, `created_at`, `updated_at` |
| **Optional fields** | `description`, `applies_to_document_types` (array), `effective_from`, `effective_to`, `requires_llm_judgment` (bool), `retired_at` |
| **Relationships** | N → 1 `Customer`; referenced by `ValidationCheck.rule_id` |
| **Invariants** | `definition_json` schema-validated; crisp checks set `requires_llm_judgment = false`; overlapping active identical `rule_key` forbidden; retired rules remain for historical FK integrity |
| **Audit** | Activate/retire/update definition audited with actor |
| **Class** | Business data (configuration) |

---

### 7. Validation

| Aspect | Definition |
|--------|------------|
| **Purpose** | Aggregate validation result for a verification run over a **document set** (Part 1: usually one document; Part 2: many). |
| **Lifecycle** | `pending` → `running` → `completed` \| `failed`. Completed rows are immutable. |
| **Identity** | `validation_id` (UUID). Unique `(verification_run_id)` for the primary validation pass (reruns use new run ids). |
| **Required fields** | `validation_id`, `verification_run_id`, `shipment_id`, `status`, `aggregate_result`, `created_at`, `completed_at` |
| **Optional fields** | `document_version_ids` (array UUID), `summary_json`, `error_code`, `error_message` |
| **Relationships** | N → 1 shipment; 1 → N `ValidationCheck`; feeds `Decision` |
| **Invariants** | `aggregate_result` ∈ {`MATCH`, `MISMATCH`, `UNCERTAIN`} when `status = completed`; `failed` must not be treated as `MATCH`; aggregate derived from checks via documented policy (e.g. any MISMATCH → MISMATCH; else any UNCERTAIN → UNCERTAIN; else MATCH) |
| **Audit** | Completion audited with aggregate + rule-set version refs |
| **Class** | Derived aggregate + references to AI/deterministic check rows |

---

### 8. ValidationCheck

| Aspect | Definition |
|--------|------------|
| **Purpose** | One rule evaluation outcome, optionally scoped to a field and/or pair of documents (cross-doc ready). |
| **Lifecycle** | Created during validation; immutable. |
| **Identity** | `validation_check_id` (UUID). Unique `(validation_id, rule_id, check_sequence)` or equivalent natural key. |
| **Required fields** | `validation_check_id`, `validation_id`, `rule_id`, `result`, `created_at` |
| **Optional fields** | `field_key`, `extracted_field_id`, `compared_document_version_ids` (array; Part 2 cross-doc), `expected_json`, `actual_json`, `reason_code`, `reason_detail`, `evaluator` (`deterministic` \| `llm`), `confidence`, `model_call_id` |
| **Relationships** | N → 1 `Validation`; N → 1 `CustomerRule`; optional FK to `ExtractedField` |
| **Invariants** | `result` ∈ {`MATCH`, `MISMATCH`, `UNCERTAIN`}; LLM evaluator rows must carry `model_call_id` or explicit metadata; cross-doc checks list ≥ 2 version ids when used; do not store the only explanation as unstructured text—`reason_code` required, `reason_detail` optional |
| **Audit** | Covered by parent validation completion; individual checks remain queryable |
| **Class** | Mix: deterministic outcomes are derived; LLM-assisted reasons/confidence are AI-generated |

---

### 9. Decision

| Aspect | Definition |
|--------|------------|
| **Purpose** | Router disposition for a verification run, retained as an append-only history so Part 2 human approval can add transitions without rewriting the router outcome. |
| **Lifecycle** | `proposed` (router write) → optionally `superseded` by later run; Part 2 may add linked **approval** records without mutating this row’s disposition. |
| **Identity** | `decision_id` (UUID). |
| **Required fields** | `decision_id`, `verification_run_id`, `shipment_id`, `disposition`, `decided_at`, `policy_version`, `created_at` |
| **Optional fields** | `validation_id`, `reasoning_json` (structured factors), `reasoning_summary` (short text), `risk_flags` (array), `model_call_id`, `supersedes_decision_id`, `actor_type` (`router` \| `system_failsafe`) |
| **Relationships** | N → 1 shipment; N → 1 verification run; optional N → 1 validation; Part 2: 1 → N approvals / outbound actions (reserved) |
| **Invariants** | `disposition` ∈ {`AUTO_APPROVE`, `HUMAN_REVIEW`, `AMENDMENT_REQUEST`}; fail-safe / stage failure must not persist `AUTO_APPROVE`; `reasoning_json` lists typed contributing factors (validation aggregate, low-confidence fields, rule ids)—not only prose; historical decisions are never overwritten |
| **Audit** | Every decision insert emits `AuditEvent`; Part 2 approvals are separate audited entities |
| **Class** | AI-generated reasoning + derived disposition from policy |

---

### 10. AuditEvent

| Aspect | Definition |
|--------|------------|
| **Purpose** | Immutable security/operations trail for reconstructability (“why was this approved?”). |
| **Lifecycle** | Insert-only. |
| **Identity** | `audit_event_id` (UUID / bigserial). |
| **Required fields** | `audit_event_id`, `occurred_at`, `actor_type`, `action`, `entity_type`, `entity_id` |
| **Optional fields** | `actor_id`, `shipment_id`, `verification_run_id`, `customer_id`, `payload_json` (redacted), `correlation_id`, `ip` / `user_agent` (if human UI) |
| **Relationships** | Soft references to domain entities by type+id; no cascade delete from business tables |
| **Invariants** | No updates/deletes in application path; payloads exclude secrets and minimize raw document PII (prefer ids, hashes, field keys); `action` from controlled vocabulary |
| **Audit** | N/A (this *is* the audit stream) |
| **Class** | **Audit data** |

---

## Supporting entities (required for a coherent store)

These are not optional inventiveness—they make the named entities workable, idempotent, and Part 2-ready. They are still documentation-only in this phase (no repositories).

### VerificationRun

Pipeline execution bound to a shipment (and the document versions processed).

| Aspect | Definition |
|--------|------------|
| **Purpose** | Correlation id for extraction → validation → routing; idempotency and cost/trace anchor. |
| **Identity** | `verification_run_id` (UUID). Unique `idempotency_key` when provided. |
| **Required** | `shipment_id`, `status`, `created_at` |
| **Optional** | `idempotency_key`, `trigger` (`upload` \| `api` \| `email` \| `replay`), `started_at`, `completed_at`, `error_code` |
| **Class** | Business / operational metadata |

### ModelCallMetadata

| Aspect | Definition |
|--------|------------|
| **Purpose** | Queryable model/prompt/version/cost metadata for reproducibility (`REQ-AI-006`). |
| **Required** | `model_call_id`, `stage` (`extraction` \| `validation_llm` \| `routing`), `provider`, `model_name`, `prompt_version`, `created_at` |
| **Optional** | `temperature`, `token_input`, `token_output`, `cost_usd`, `latency_ms`, `request_hash`, `response_schema_version` |
| **Class** | AI-generated / AI-ops metadata (not free-form chat logs) |

### Part 2 reserved (tables documented, not implemented now)

| Entity | Role |
|--------|------|
| `IngestionMessage` | Email/file trigger envelope |
| `CommunicationDraft` | Draft amendment replies |
| `DecisionApproval` | Human approval gate before outbound |
| `OutboundAction` | Send attempts and results |

Schema placeholders and nullability are specified in [schema-design.md](./schema-design.md) so Part 1 need not rewrite history.

---

## Cross-cutting invariants

1. **Shipment 1→N documents** always; never embed a single file as the shipment row.
2. **Document content is versioned**; pipeline stages pin `document_version_id`.
3. **AI outputs are append-only** per run; fixes = new run/version.
4. **Decisions are append-only**; Part 2 approval is additive.
5. **Idempotent ingest**: same idempotency key or same `(shipment_id, content_sha256, document_type)` does not create unbounded duplicates.
6. **Fail-safe storage**: failed runs may exist without `AUTO_APPROVE` decisions.
7. **Queryable structure**: enums + JSON Schema–validated JSONB for flexible payloads; critical filter fields are real columns.

---

## Related requirements

- `REQ-DATA-001` … `REQ-DATA-004`
- `REQ-VAL-006`, `REQ-AI-006`, `REQ-OBS-002`
- `REQ-PART2-001` … `REQ-PART2-007`
- Architecture: Part 2 extension points, auditability, idempotency principles
