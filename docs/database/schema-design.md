# Schema design (PostgreSQL)

Physical design for Nova’s system of record. **No migrations or application code in this phase**—this is the contract for Phase 5 persistence work.

Aligned with [domain-model.md](./domain-model.md) and [ADR-0003](../decisions/0003-database.md).

---

## Conventions

| Topic | Choice |
|-------|--------|
| DBMS | PostgreSQL 16+ (target) |
| PK type | `UUID` primary keys (`gen_random_uuid()`) except optional bigserial for high-volume `audit_events` |
| Timestamps | `TIMESTAMPTZ` always |
| Enums | PostgreSQL `ENUM` types **or** `TEXT` + `CHECK` (prefer `TEXT` + `CHECK` early for migration agility) |
| Flexible payloads | `JSONB` with application-level JSON Schema validation before insert |
| Money / decimals | Prefer numeric strings in JSON for extracted amounts **plus** optional `NUMERIC` normalized columns later—do not use binary float |
| Soft delete | `deleted_at TIMESTAMPTZ NULL` on `customers`, `documents`, `customer_rules` (see policy below) |
| Hard delete | Forbidden for `audit_events`, `decisions`, completed `validations` / checks, `document_versions`, `extracted_fields` in app paths |
| Naming | `snake_case` tables and columns; singular entity names mapped to plural table names |

---

## Soft-delete policy

| Table | Policy |
|-------|--------|
| `customers` | Soft delete; block new shipments |
| `customer_rules` | Soft delete / `retired`; FK from historical checks retained |
| `documents` | Soft delete (withdrawn); versions retained |
| `shipments` | Soft close preferred (`status = closed`); soft delete only if never decided |
| AI & decision tables | **No soft delete**—new runs supersede |
| `audit_events` | No delete |

---

## Enumerations (logical)

```text
customer_status:          draft | active | suspended | archived
shipment_status:          open | ingesting | extracting | validating | routing | decided | closed
document_status:          registered | content_available | in_pipeline | extracted | superseded | withdrawn
document_type:            commercial_invoice | bill_of_lading | packing_list | other
ingestion_channel:        upload | path | email | api
rule_status:              draft | active | retired
check_kind:               equality | presence | numeric_tolerance | allowlist | cross_field | cross_document | custom
rule_severity:            info | warn | block
validation_status:        pending | running | completed | failed
validation_result:        MATCH | MISMATCH | UNCERTAIN
decision_disposition:     AUTO_APPROVE | HUMAN_REVIEW | AMENDMENT_REQUEST
actor_type:               human | system | router | extractor | validator | api
verification_run_status:  queued | running | succeeded | failed | cancelled
```

---

## Tables

### `customers`

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `customer_id` | UUID | PK | |
| `name` | TEXT | NO | CHECK length > 0 |
| `external_key` | TEXT | YES | UNIQUE when not null |
| `status` | TEXT | NO | CHECK enum |
| `default_timezone` | TEXT | YES | |
| `metadata` | JSONB | NO | DEFAULT `{}` |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |
| `archived_at` | TIMESTAMPTZ | YES | |
| `deleted_at` | TIMESTAMPTZ | YES | |

---

### `shipments`

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `shipment_id` | UUID | PK | |
| `customer_id` | UUID | NO | FK → `customers` |
| `customer_shipment_ref` | TEXT | YES | |
| `status` | TEXT | NO | |
| `priority` | INT | YES | |
| `metadata` | JSONB | NO | DEFAULT `{}` |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |
| `closed_at` | TIMESTAMPTZ | YES | |
| `deleted_at` | TIMESTAMPTZ | YES | |

**Uniqueness:** `UNIQUE (customer_id, customer_shipment_ref)` where `customer_shipment_ref IS NOT NULL`.

---

### `documents`

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `document_id` | UUID | PK | |
| `shipment_id` | UUID | NO | FK → `shipments` |
| `document_type` | TEXT | NO | |
| `status` | TEXT | NO | |
| `display_name` | TEXT | YES | |
| `source_system` | TEXT | YES | |
| `ingestion_channel` | TEXT | NO | DEFAULT `upload` |
| `current_version_id` | UUID | YES | FK → `document_versions` (deferred circular FK) |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |
| `deleted_at` | TIMESTAMPTZ | YES | |

**Part 2:** Multiple rows per `shipment_id` are first-class; no unique constraint forcing one doc per shipment.

---

### `document_versions`

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `document_version_id` | UUID | PK | |
| `document_id` | UUID | NO | FK → `documents` |
| `version_number` | INT | NO | CHECK > 0 |
| `storage_uri` | TEXT | NO | Object store URI; no secrets |
| `content_sha256` | CHAR(64) | NO | Hex digest |
| `media_type` | TEXT | NO | |
| `byte_size` | BIGINT | NO | CHECK ≥ 0 |
| `original_filename` | TEXT | YES | |
| `page_count` | INT | YES | |
| `ingestion_idempotency_key` | TEXT | YES | |
| `source_message_id` | TEXT | YES | Part 2 email Message-ID |
| `created_by` | TEXT | YES | |
| `created_at` | TIMESTAMPTZ | NO | |

**Uniqueness**

- `UNIQUE (document_id, version_number)`
- `UNIQUE (ingestion_idempotency_key)` where not null
- **Duplicate document guard (shipment-scoped):** unique index on `(shipment_id, document_type, content_sha256)` via join or denormalized `shipment_id` column on versions for enforcement:

Recommended denormalization for constraint clarity:

| Extra column | Type | Notes |
|--------------|------|-------|
| `shipment_id` | UUID | NO, FK → `shipments`, must match parent document’s shipment |

`UNIQUE (shipment_id, document_type, content_sha256)` — prevents unbounded duplicate identical files of the same type on one shipment. Re-processing the same bytes is idempotent (return existing version/document).

---

### `verification_runs`

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `verification_run_id` | UUID | PK | |
| `shipment_id` | UUID | NO | FK → `shipments` |
| `status` | TEXT | NO | |
| `idempotency_key` | TEXT | YES | UNIQUE |
| `trigger` | TEXT | NO | |
| `document_version_ids` | UUID[] | NO | Versions included in this run |
| `started_at` | TIMESTAMPTZ | YES | |
| `completed_at` | TIMESTAMPTZ | YES | |
| `error_code` | TEXT | YES | |
| `error_message` | TEXT | YES | |
| `created_at` | TIMESTAMPTZ | NO | |

---

### `model_call_metadata`

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `model_call_id` | UUID | PK | |
| `verification_run_id` | UUID | NO | FK |
| `stage` | TEXT | NO | |
| `provider` | TEXT | NO | |
| `model_name` | TEXT | NO | |
| `prompt_version` | TEXT | NO | |
| `response_schema_version` | TEXT | YES | |
| `temperature` | NUMERIC | YES | |
| `token_input` | INT | YES | |
| `token_output` | INT | YES | |
| `cost_usd` | NUMERIC(12,6) | YES | |
| `latency_ms` | INT | YES | |
| `request_hash` | TEXT | YES | |
| `created_at` | TIMESTAMPTZ | NO | |

Do **not** store full prompts with raw document PII by default; store version ids + hashes. Full prompt archives, if ever needed, belong in a restricted store with retention controls.

---

### `extracted_fields`

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `extracted_field_id` | UUID | PK | |
| `verification_run_id` | UUID | NO | FK |
| `document_version_id` | UUID | NO | FK |
| `field_key` | TEXT | NO | e.g. `invoice_number` |
| `value_json` | JSONB | YES | Null if missing |
| `value_type` | TEXT | NO | `string` \| `number` \| `date` \| `object` \| … |
| `normalized_value_json` | JSONB | YES | Derived |
| `confidence` | NUMERIC(4,3) | YES | CHECK 0–1 |
| `evidence_json` | JSONB | NO | Structured evidence |
| `is_missing` | BOOLEAN | NO | DEFAULT false |
| `absence_reason` | TEXT | YES | |
| `extractor_notes` | TEXT | YES | Short; not the SoR |
| `model_call_id` | UUID | YES | FK |
| `created_at` | TIMESTAMPTZ | NO | |

**Uniqueness:** `UNIQUE (verification_run_id, document_version_id, field_key)`  
**CHECK:** `NOT is_missing OR value_json IS NULL`  
**CHECK:** `confidence IS NOT NULL OR absence_reason IS NOT NULL`

---

### `customer_rules`

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `customer_rule_id` | UUID | PK | |
| `customer_id` | UUID | NO | FK |
| `rule_key` | TEXT | NO | Stable key across versions |
| `rule_version` | INT | NO | |
| `status` | TEXT | NO | |
| `check_kind` | TEXT | NO | |
| `severity` | TEXT | NO | |
| `definition_json` | JSONB | NO | |
| `description` | TEXT | YES | |
| `applies_to_document_types` | TEXT[] | YES | |
| `requires_llm_judgment` | BOOLEAN | NO | DEFAULT false |
| `effective_from` | TIMESTAMPTZ | YES | |
| `effective_to` | TIMESTAMPTZ | YES | |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |
| `retired_at` | TIMESTAMPTZ | YES | |
| `deleted_at` | TIMESTAMPTZ | YES | |

**Uniqueness:** `UNIQUE (customer_id, rule_key, rule_version)`  
**Partial unique:** one `active` row per `(customer_id, rule_key)`:

```sql
CREATE UNIQUE INDEX customer_rules_one_active
  ON customer_rules (customer_id, rule_key)
  WHERE status = 'active' AND deleted_at IS NULL;
```

---

### `validations`

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `validation_id` | UUID | PK | |
| `verification_run_id` | UUID | NO | FK, UNIQUE for primary pass |
| `shipment_id` | UUID | NO | FK |
| `status` | TEXT | NO | |
| `aggregate_result` | TEXT | YES | Required when completed |
| `document_version_ids` | UUID[] | NO | Multi-doc ready |
| `summary_json` | JSONB | YES | Counts, flags |
| `error_code` | TEXT | YES | |
| `error_message` | TEXT | YES | |
| `created_at` | TIMESTAMPTZ | NO | |
| `completed_at` | TIMESTAMPTZ | YES | |

**CHECK:** `(status <> 'completed') OR (aggregate_result IN ('MATCH','MISMATCH','UNCERTAIN'))`  
**CHECK:** `(status <> 'failed') OR (aggregate_result IS NULL OR aggregate_result <> 'MATCH')` — failed runs must not look like clean MATCH.

---

### `validation_checks`

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `validation_check_id` | UUID | PK | |
| `validation_id` | UUID | NO | FK ON DELETE CASCADE (only while parent not completed—prefer RESTRICT after complete) |
| `rule_id` | UUID | NO | FK → `customer_rules` |
| `check_sequence` | INT | NO | |
| `result` | TEXT | NO | MATCH / MISMATCH / UNCERTAIN |
| `field_key` | TEXT | YES | |
| `extracted_field_id` | UUID | YES | FK |
| `compared_document_version_ids` | UUID[] | YES | Cross-doc |
| `expected_json` | JSONB | YES | |
| `actual_json` | JSONB | YES | |
| `reason_code` | TEXT | NO | |
| `reason_detail` | TEXT | YES | |
| `evaluator` | TEXT | NO | deterministic \| llm |
| `confidence` | NUMERIC(4,3) | YES | |
| `model_call_id` | UUID | YES | FK |
| `created_at` | TIMESTAMPTZ | NO | |

**Uniqueness:** `UNIQUE (validation_id, rule_id, check_sequence)`  
**CHECK:** cross-doc kinds should use array length ≥ 2 when `check_kind` implies cross-document (enforced in app + optional trigger later).

---

### `decisions`

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `decision_id` | UUID | PK | |
| `verification_run_id` | UUID | NO | FK |
| `shipment_id` | UUID | NO | FK |
| `validation_id` | UUID | YES | FK |
| `disposition` | TEXT | NO | |
| `policy_version` | TEXT | NO | |
| `reasoning_json` | JSONB | NO | Structured factors |
| `reasoning_summary` | TEXT | YES | |
| `risk_flags` | TEXT[] | YES | |
| `actor_type` | TEXT | NO | router \| system_failsafe |
| `model_call_id` | UUID | YES | FK |
| `supersedes_decision_id` | UUID | YES | FK → `decisions` |
| `decided_at` | TIMESTAMPTZ | NO | |
| `created_at` | TIMESTAMPTZ | NO | |

**Uniqueness:** `UNIQUE (verification_run_id)` — one router decision per run; later human approval is a **different table**.  
**CHECK:** failsafe actor cannot write `AUTO_APPROVE` (app + DB check recommended):

```sql
CHECK (actor_type <> 'system_failsafe' OR disposition <> 'AUTO_APPROVE')
```

---

### `audit_events`

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `audit_event_id` | BIGSERIAL | PK | Or UUID |
| `occurred_at` | TIMESTAMPTZ | NO | DEFAULT now() |
| `actor_type` | TEXT | NO | |
| `actor_id` | TEXT | YES | |
| `action` | TEXT | NO | |
| `entity_type` | TEXT | NO | |
| `entity_id` | TEXT | NO | |
| `customer_id` | UUID | YES | |
| `shipment_id` | UUID | YES | |
| `verification_run_id` | UUID | YES | |
| `correlation_id` | TEXT | YES | |
| `payload_json` | JSONB | NO | DEFAULT `{}`, redacted |
| `created_at` | TIMESTAMPTZ | NO | DEFAULT now() |

No FKs required to business tables (survive entity removal). Optional FKs with `ON DELETE SET NULL` are acceptable if preferred for integrity—**never CASCADE delete audit rows**.

---

## Part 2 reserved tables (create empty / stub migrations later)

### `ingestion_messages`

Email/file envelopes: `ingestion_message_id`, `customer_id`, `shipment_id` nullable, `channel`, `external_message_id` UNIQUE, `received_at`, `raw_headers_uri`, `status`.

### `communication_drafts`

`draft_id`, `shipment_id`, `decision_id`, `body_text`, `body_structured_json`, `status` (`draft` \| `approved` \| `rejected` \| `sent`), `created_at`.

### `decision_approvals`

`approval_id`, `decision_id`, `approver_id`, `outcome` (`approved` \| `rejected`), `notes`, `created_at`.  
Does **not** mutate `decisions.disposition`.

### `outbound_actions`

`outbound_action_id`, `draft_id`, `approval_id`, `channel`, `status`, `provider_message_id`, `attempted_at`, `error_code`.

Part 1 must not write these tables; their presence in the design prevents painting into a corner.

---

## Transaction boundaries (logical)

| Unit of work | Must commit together | On failure |
|--------------|----------------------|------------|
| Register document + first version | `documents` + `document_versions` + `current_version_id` update | Roll back both |
| Complete extraction | All `extracted_fields` for run+versions + `model_call_metadata` + run status advance | No partial field set visible as “complete” |
| Complete validation | `validations` + all `validation_checks` + aggregate | Mark `failed`, no fake MATCH |
| Persist decision | `decisions` + `audit_events` + shipment status | No decision without audit row |
| Idempotent re-ingest | Lookup by idempotency/hash inside transaction with upsert/select | Return existing ids |

Partial stage failure: leave run `failed`, emit audit, **do not** insert `AUTO_APPROVE`.

---

## AI data storage rules

| Concern | Storage |
|---------|---------|
| Extracted values | `value_json` + `value_type` + optional normalized column |
| Confidence | Numeric column |
| Evidence | `evidence_json` structured |
| Validation | Enum `result` + `reason_code` + structured expected/actual |
| Decision reasoning | `reasoning_json` (factors[], thresholds, rule_ids) |
| Model metadata | `model_call_metadata` row |
| Prompt version | `prompt_version` text id, not full prompt body by default |

---

## Related

- [relationships.md](./relationships.md)
- [indexing-strategy.md](./indexing-strategy.md)
- [audit-model.md](./audit-model.md)
- [database-test-plan.md](./database-test-plan.md)
