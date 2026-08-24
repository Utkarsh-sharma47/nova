# Indexing strategy

Indexes for Nova’s PostgreSQL schema. Prefer **selective, workload-driven** indexes; avoid indexing every JSONB path up front.

Baseline assumes Part 1 query patterns: lookup by shipment, review queue by disposition, field/evidence inspection, rule application, idempotent ingest.

---

## Principles

1. Every PK is indexed by definition; every UNIQUE constraint creates an index.
2. Index foreign keys used in joins and `ON DELETE` checks.
3. Partial indexes for soft-delete and “active only” filters.
4. JSONB: index **known** filter paths with expressions or GIN only when a query needs them.
5. Audit table: time-bracketing + entity lookup; partition later if volume demands (not required for Part 1).

---

## Required unique / primary indexes

| Table | Index | Purpose |
|-------|-------|---------|
| All | PK | Identity |
| `customers` | `UNIQUE (external_key)` WHERE NOT NULL | External idempotent upsert |
| `shipments` | `UNIQUE (customer_id, customer_shipment_ref)` WHERE ref NOT NULL | Customer-facing reference |
| `document_versions` | `UNIQUE (document_id, version_number)` | Version chain |
| `document_versions` | `UNIQUE (ingestion_idempotency_key)` WHERE NOT NULL | Ingest idempotency |
| `document_versions` | `UNIQUE (shipment_id, document_type, content_sha256)` | Duplicate document guard |
| `verification_runs` | `UNIQUE (idempotency_key)` WHERE NOT NULL | Run idempotency |
| `extracted_fields` | `UNIQUE (verification_run_id, document_version_id, field_key)` | One value per field per run |
| `customer_rules` | `UNIQUE (customer_id, rule_key, rule_version)` | Rule versioning |
| `customer_rules` | Partial UNIQUE `(customer_id, rule_key)` WHERE `status = 'active' AND deleted_at IS NULL` | One active rule |
| `validations` | `UNIQUE (verification_run_id)` | One primary validation per run |
| `validation_checks` | `UNIQUE (validation_id, rule_id, check_sequence)` | Stable check identity |
| `decisions` | `UNIQUE (verification_run_id)` | One router decision per run |

---

## Foreign-key and access-path indexes

| Table | Index | Query pattern |
|-------|-------|---------------|
| `shipments` | `(customer_id, created_at DESC)` | Customer shipment list |
| `shipments` | `(status, updated_at DESC)` WHERE `deleted_at IS NULL` | Ops queues by status |
| `documents` | `(shipment_id)` | Docs for shipment |
| `documents` | `(shipment_id, document_type)` WHERE `deleted_at IS NULL` | Find invoice/BOL |
| `document_versions` | `(document_id, version_number DESC)` | Latest versions |
| `document_versions` | `(content_sha256)` | Global hash lookup (optional) |
| `verification_runs` | `(shipment_id, created_at DESC)` | Run history |
| `verification_runs` | `(status, created_at DESC)` | Stuck/failed runs |
| `extracted_fields` | `(document_version_id)` | All fields for a version |
| `extracted_fields` | `(verification_run_id)` | All fields for a run |
| `extracted_fields` | `(field_key, verification_run_id)` | Point lookup |
| `customer_rules` | `(customer_id)` WHERE `status = 'active' AND deleted_at IS NULL` | Load rule set |
| `validations` | `(shipment_id, created_at DESC)` | History |
| `validation_checks` | `(validation_id)` | Load checks |
| `validation_checks` | `(rule_id)` | Rule effectiveness analytics |
| `validation_checks` | `(result)` partial WHERE `result IN ('MISMATCH','UNCERTAIN')` | Review tooling (optional) |
| `decisions` | `(shipment_id, decided_at DESC)` | Decision history |
| `decisions` | `(disposition, decided_at DESC)` | **HUMAN_REVIEW queue** |
| `model_call_metadata` | `(verification_run_id)` | Cost/trace per run |
| `model_call_metadata` | `(created_at DESC)` | Cost reporting windows |

---

## Audit indexes

| Index | Purpose |
|-------|---------|
| `(occurred_at DESC)` | Time-range scan |
| `(entity_type, entity_id, occurred_at DESC)` | Reconstruct entity history |
| `(shipment_id, occurred_at DESC)` WHERE shipment_id IS NOT NULL | Shipment timeline |
| `(verification_run_id)` WHERE NOT NULL | Run audit trail |
| `(customer_id, occurred_at DESC)` WHERE NOT NULL | Tenant audit |

---

## JSONB strategy

| Column | Approach | When |
|--------|----------|------|
| `evidence_json` | No GIN by default; query via parent field row | Part 1 |
| `definition_json` | Expression indexes only if rules engine filters on a stable path | Later |
| `reasoning_json` | Keep filterable factors also in `risk_flags` / disposition columns | Prefer columns |
| `metadata` | GIN only if product search requires it | Defer |
| `value_json` | Prefer `normalized_value_json` + typed columns for hot fields later | Phase 5+ |

If NL query needs text search, add a **separate** search document table or `tsvector` column in Phase 6—do not overload operational indexes.

---

## Confidence / review helpers

```sql
-- Low-confidence extractions for a run (expression/partial as needed)
CREATE INDEX extracted_fields_low_confidence
  ON extracted_fields (verification_run_id, confidence)
  WHERE confidence IS NOT NULL AND confidence < 0.80;
```

Threshold is illustrative; product policy owns the real cutoff—index can be adjusted without schema redesign.

---

## Anti-patterns

- Indexing every FK “just in case” on tiny tables (wasteful writes)—still index FKs that PostgreSQL needs for deletes/joins on hot paths.
- Unique constraints that force **one document per shipment**.
- Unique on `content_sha256` alone globally (same file may appear for different customers/shipments).
- Updating rows to “change” index identity for AI outputs—use new runs instead.

---

## Related

- [schema-design.md](./schema-design.md)
- [database-test-plan.md](./database-test-plan.md)
