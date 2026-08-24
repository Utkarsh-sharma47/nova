# Database test plan

Defines **required database tests** for Nova’s schema. This is a specification only—**do not treat as implemented**. Repositories and full persistence code are out of scope until Phase 5.

Related: [schema-design.md](./schema-design.md), [indexing-strategy.md](./indexing-strategy.md), testing philosophy under `docs/testing/`.

---

## Goals

Prove that PostgreSQL constraints and transaction boundaries protect domain invariants:

- Referential integrity
- Uniqueness / idempotency
- Duplicate document prevention
- Partial failure safety (no false `AUTO_APPROVE` / false complete extraction)
- Append-only behavior for AI and audit rows where required

---

## Test environment (when implemented)

| Item | Expectation |
|------|-------------|
| Database | PostgreSQL matching ADR-0002 (container or ephemeral instance) |
| Migrations | Apply from clean slate each suite (or transactional DDL strategy) |
| Honesty | Tests must fail if constraints are dropped or weakened |
| Scope | Schema/constraint tests first; repository tests later |

---

## 1. Foreign key tests

| ID | Scenario | Expectation |
|----|----------|-------------|
| DB-FK-001 | Insert `shipment` with unknown `customer_id` | Reject |
| DB-FK-002 | Insert `document` with unknown `shipment_id` | Reject |
| DB-FK-003 | Insert `document_version` with unknown `document_id` | Reject |
| DB-FK-004 | Set `documents.current_version_id` to version of **another** document | Reject (CHECK/trigger or app+constraint) |
| DB-FK-005 | Insert `extracted_field` with version not in run’s shipment | Reject or fail app invariant test |
| DB-FK-006 | Insert `validation_check` with unknown `rule_id` | Reject |
| DB-FK-007 | Delete `customer_rule` still referenced by `validation_checks` | Reject (RESTRICT) |
| DB-FK-008 | Delete `shipment` with existing `decisions` | Reject or soft-delete path only |

---

## 2. Constraint / check tests

| ID | Scenario | Expectation |
|----|----------|-------------|
| DB-CK-001 | `extracted_fields.confidence = 1.5` | Reject |
| DB-CK-002 | `is_missing = true` with non-null `value_json` | Reject |
| DB-CK-003 | `confidence` null without `absence_reason` | Reject |
| DB-CK-004 | `validations.status = completed` with null `aggregate_result` | Reject |
| DB-CK-005 | `validations.status = failed` with `aggregate_result = MATCH` | Reject |
| DB-CK-006 | `decisions.actor_type = system_failsafe` and `disposition = AUTO_APPROVE` | Reject |
| DB-CK-007 | `validation_checks.result` not in MATCH/MISMATCH/UNCERTAIN | Reject |
| DB-CK-008 | `decisions.disposition` not in allowed router set | Reject |
| DB-CK-009 | `document_versions.version_number = 0` | Reject |

---

## 3. Uniqueness tests

| ID | Scenario | Expectation |
|----|----------|-------------|
| DB-UQ-001 | Two customers with same `external_key` | Reject |
| DB-UQ-002 | Two shipments same `(customer_id, customer_shipment_ref)` | Reject |
| DB-UQ-003 | Two versions same `(document_id, version_number)` | Reject |
| DB-UQ-004 | Two active `customer_rules` same `(customer_id, rule_key)` | Reject |
| DB-UQ-005 | Two `extracted_fields` same `(run, version, field_key)` | Reject |
| DB-UQ-006 | Two `validations` same `verification_run_id` | Reject |
| DB-UQ-007 | Two `decisions` same `verification_run_id` | Reject |
| DB-UQ-008 | Two runs same `idempotency_key` | Reject |

---

## 4. Duplicate document tests

| ID | Scenario | Expectation |
|----|----------|-------------|
| DB-DUP-001 | Second `document_version` same `(shipment_id, document_type, content_sha256)` | Reject at DB **or** idempotent API returns existing row (test both layers when repos exist) |
| DB-DUP-002 | Same hash, **different** `document_type` on same shipment | Allowed (e.g. mis-tagged types still distinct logical docs—product may still warn) |
| DB-DUP-003 | Same hash on **different** shipments | Allowed |
| DB-DUP-004 | Part 1 path: two different hashes → two documents on one shipment | Allowed (multi-doc readiness) |

---

## 5. Transaction boundary tests

| ID | Scenario | Expectation |
|----|----------|-------------|
| DB-TX-001 | Insert document then fail version insert; commit | No orphan document **or** document remains `registered` without current version—define one behavior and assert it |
| DB-TX-002 | Extraction transaction inserts N−1 fields then errors | No run marked `succeeded`; no partial “complete” extraction visible |
| DB-TX-003 | Validation checks inserted then failure before aggregate | Validation not `completed` with MATCH; status `failed` or rolled back |
| DB-TX-004 | Decision insert without audit event in same unit of work | Fail test if app commits decision alone (application-level transactional test) |
| DB-TX-005 | Concurrent dual insert same idempotency key | Exactly one run/version wins; other hits unique violation and retries read |

---

## 6. Partial failure / fail-safe tests

| ID | Scenario | Expectation |
|----|----------|-------------|
| DB-PF-001 | Run `failed` after extraction timeout | Zero `decisions` with `AUTO_APPROVE` for that run |
| DB-PF-002 | Validation `failed` | No completed MATCH aggregate |
| DB-PF-003 | Router failsafe path | Only `HUMAN_REVIEW` (or non-approve disposition) + audit `decision.failsafe` |
| DB-PF-004 | Missing evidence / low confidence persisted correctly | Fields queryable; not upgraded in DB to high confidence |

---

## 7. Idempotency tests

| ID | Scenario | Expectation |
|----|----------|-------------|
| DB-ID-001 | Replay ingest with same `ingestion_idempotency_key` | Single version row |
| DB-ID-002 | Replay verification with same run `idempotency_key` | Single run; no duplicate extractions |
| DB-ID-003 | Legitimate re-process after content change (new hash) | New version_number; prior version retained |
| DB-ID-004 | Amendment creates new version and new run | Prior `decisions` rows remain; new decision may `supersedes_decision_id` |

---

## 8. Append-only / audit tests

| ID | Scenario | Expectation |
|----|----------|-------------|
| DB-AO-001 | UPDATE on `audit_events` via app role | Denied (permissions) or absent from API |
| DB-AO-002 | UPDATE `decisions.disposition` after insert | Denied by convention/test (no repository method); history via new rows |
| DB-AO-003 | Soft-delete customer | Prior audit + decisions still readable |
| DB-AO-004 | Part 2 approval simulation | Insert `decision_approvals` without mutating router disposition |

---

## 9. Multi-document readiness tests

| ID | Scenario | Expectation |
|----|----------|-------------|
| DB-MD-001 | Two documents on one shipment | Both persist |
| DB-MD-002 | Validation with `document_version_ids` length 2 | Persists |
| DB-MD-003 | Check with `compared_document_version_ids` length 2 | Persists |
| DB-MD-004 | Run including both versions’ extracted fields | Unique per version+field_key |

---

## Out of scope for this plan

- LLM quality / eval harnesses
- Full repository CRUD suites (add when implementing)
- UI tests
- Load/performance SLOs (add when needed)

---

## Verification status (this delivery)

| Item | Status |
|------|--------|
| Test plan documented | Yes |
| Tests implemented | **No** (no application DB yet) |
| Tests executed | **Not applicable** |

Do not claim CI database green until these tests exist and run.
