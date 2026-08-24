# Audit model

How Nova records **who did what, when, and why** for trade-document verification. Complements [domain-model.md](./domain-model.md) and `audit_events` in [schema-design.md](./schema-design.md).

---

## Goals

1. Reconstruct why a shipment received `AUTO_APPROVE`, `HUMAN_REVIEW`, or `AMENDMENT_REQUEST`.
2. Show which rule versions, extracted fields, evidence, and policy versions participated.
3. Support security review (who changed customer rules; who withdrew a document).
4. Survive soft-deletes of business entities.
5. Avoid turning the audit table into a second copy of full document bytes or secrets.

---

## Two layers of auditability

| Layer | Mechanism | Answers |
|-------|-----------|---------|
| **Domain history** | Append-only business/AI tables (`document_versions`, `extracted_fields`, `validation_checks`, `decisions`) | What were the structured facts and outcomes? |
| **Audit stream** | `audit_events` | Who/what triggered state changes; correlation across stages |

Reviewers should prefer domain history for field-level evidence. Use `audit_events` for control-plane actions and stage lifecycle.

---

## What must be audited

| Action | `action` (example) | Entity | Payload highlights (redacted) |
|--------|--------------------|--------|-------------------------------|
| Customer created/updated/archived | `customer.created` / `.updated` / `.archived` | Customer | status transitions |
| Rule activated/retired | `rule.activated` / `.retired` | CustomerRule | `rule_key`, `rule_version` |
| Document registered | `document.registered` | Document | type, channel |
| Version added | `document_version.created` | DocumentVersion | sha256, version_number, byte_size |
| Verification run started/finished | `run.started` / `.succeeded` / `.failed` | VerificationRun | error_code |
| Extraction completed | `extraction.completed` | VerificationRun | field count, model/prompt versions |
| Validation completed | `validation.completed` | Validation | aggregate_result, check counts |
| Decision recorded | `decision.recorded` | Decision | disposition, policy_version, actor_type |
| Fail-safe halt | `decision.failsafe` | Decision / Run | reason codes |
| Part 2 (later) approval / send | `approval.*` / `outbound.*` | reserved entities | outcome, channel |

---

## Actor model

| `actor_type` | Meaning |
|--------------|---------|
| `human` | Ops user via UI/API |
| `api` | Machine credential |
| `extractor` / `validator` / `router` | Pipeline stage |
| `system` | Jobs, migrations, fail-safe |

`actor_id` is a stable subject id (user id, service name)—never an API key.

---

## Payload rules

**Include**

- Entity ids, shipment/run correlation ids
- Enum transitions (`status_from` → `status_to`)
- Counts and hashes
- Policy/rule/prompt **version identifiers**
- Reason codes

**Exclude**

- Provider API keys, auth headers
- Full document bytes or full OCR text dumps
- Raw prompts that embed full document content (prefer `prompt_version` + `request_hash`)
- Unnecessary PII (prefer field keys + hashes over party names in audit payloads when domain tables already store values)

---

## Immutability and retention

- Application **UPDATE/DELETE** on `audit_events` is forbidden.
- Retention: define operational window in security/ops later (`REQ-DATA-004`); archival may move partitions to cold storage **without rewriting** event bodies.
- Legal hold: stop purge jobs for listed `shipment_id` / `customer_id`.

---

## Correlation

Every pipeline stage should propagate:

- `verification_run_id`
- `shipment_id`
- `correlation_id` / trace id (also in structured logs)

`audit_events.verification_run_id` and observability traces must join on the same ids ([architecture principles](../architecture/): observability + auditability).

---

## Decision reconstructability checklist

Given `shipment_id`, an auditor can:

1. List `verification_runs` ordered by time.
2. For the relevant run, load `extracted_fields` with `confidence` + `evidence_json`.
3. Load `validations` + `validation_checks` with `rule_id` → `customer_rules.definition_json` / version.
4. Load `decisions.reasoning_json` + `disposition` + `policy_version`.
5. Confirm matching `audit_events` for `decision.recorded` (and failsafe if any).
6. Confirm **no** in-place overwrite of prior decisions (Part 2 approvals appear as additional records).

---

## Separation from AI free text

Audit and domain SoR must not depend on a single LLM paragraph. Structured columns remain authoritative; prose summaries are optional aids.

---

## Related

- [schema-design.md](./schema-design.md)
- [indexing-strategy.md](./indexing-strategy.md)
- Security baseline (`docs/security/`)
- Requirements `REQ-VAL-006`, `REQ-DATA-001`, `REQ-OBS-001`–`002`
