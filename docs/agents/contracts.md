# AI agent contracts (canonical)

Canonical typed contracts for Nova’s Extractor, Validator, and Router agents.

**Status:** Accepted design (contracts only — no runtime implementation)  
**ADR:** [ADR-0002](../decisions/0002-ai-agent-contracts-and-trust-model.md)  
**Trust model:** [trust-model.md](./trust-model.md)

This document is the **source of truth** for stage I/O shapes. Agent-specific docs ([extractor.md](./extractor.md), [validator.md](./validator.md), [router.md](./router.md)) describe behavior, failure modes, and policies that consume these contracts.

Do **not** implement LLM calls, prompts that invoke a provider, or agent runtimes in the same change that only defines these contracts.

---

## Shared primitives

### Identifiers

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Correlation ID for one verification run |
| `shipment_id` | string | Logical shipment (may be provisional in Part 1) |
| `document_id` | string | Stored document reference |
| `customer_id` | string | Customer whose rules/policy apply |

### Confidence

| Field | Type | Constraints |
|-------|------|-------------|
| `confidence` | number \| null | Inclusive range `[0.0, 1.0]` when present. `null` only when the agent explicitly cannot estimate confidence (must pair with `uncertainty` ≠ `NONE`). |

Downstream stages must treat missing or low confidence as risk, not as silence.

### FieldPresence

Distinguishes whether a value is available and how it was obtained. **Required** on every extracted field. LLMs must not collapse these into a fabricated “known” value.

| Value | Meaning | Allowed `value` |
|-------|---------|-----------------|
| `KNOWN` | Value obtained from the document with usable evidence | Non-null typed value |
| `UNKNOWN` | System cannot determine the value (illegible, unsupported, model failure after retries) | Must be `null` |
| `MISSING` | Field is expected for the document type but not present in the document | Must be `null` |
| `AMBIGUOUS` | Multiple plausible candidates; no single safe choice | Must be `null` (candidates may appear in `warnings` / `candidates`) |

**Hard rule:** `FieldPresence` other than `KNOWN` ⇒ `value` is `null`. Inventing a placeholder string/number and marking it `KNOWN` is a contract violation.

### UncertaintyFlag

Orthogonal signal for residual doubt even when a value is present.

| Value | Meaning |
|-------|---------|
| `NONE` | No residual uncertainty beyond normal confidence |
| `LOW_CONFIDENCE` | Confidence below policy threshold |
| `CONFLICTING_EVIDENCE` | Evidence spans disagree |
| `PARTIAL_EVIDENCE` | Value inferred from incomplete grounding |
| `SCHEMA_REPAIR` | Output required schema repair / coercion |
| `OTHER` | See `warnings` |

### Evidence

Grounding pointer from a value (or check) back to source material.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `evidence_id` | string | yes | Stable ID within the run |
| `document_id` | string | yes | Source document |
| `snippet` | string \| null | no | Short verbatim excerpt (PII-sensitive; redact in logs per policy) |
| `page` | integer \| null | no | 1-based page if available |
| `bbox` | object \| null | no | Optional region `{ x, y, width, height }` in document coordinates |
| `locator` | string \| null | no | Opaque locator (e.g. PDF object path, OCR block id) |
| `source_type` | enum | yes | `DOCUMENT_SPAN` \| `OCR_BLOCK` \| `TABLE_CELL` \| `DERIVED` \| `NONE` |
| `notes` | string \| null | no | Human-readable grounding note |

`source_type = NONE` is allowed only with `FieldPresence` in `{ UNKNOWN, MISSING }` or when explicitly documenting absence of evidence.

### ModelInvocationMetadata

Recorded for every LLM-backed stage call (even when the call fails).

| Field | Type | Description |
|-------|------|-------------|
| `agent_version` | string | Semver or commit-bound agent package version |
| `prompt_version` | string | Versioned prompt identifier (see [trust-model.md](./trust-model.md#prompt-governance)) |
| `model` | string | Provider model id |
| `model_provider` | string \| null | Provider name when decided |
| `temperature` | number \| null | Sampling temperature if applicable |
| `other_config` | object \| null | Non-secret generation config (top_p, max_tokens, etc.) |
| `invoked_at` | string (ISO-8601) | Invocation timestamp |
| `latency_ms` | integer \| null | End-to-end call latency |
| `input_tokens` | integer \| null | |
| `output_tokens` | integer \| null | |
| `cost_units` | number \| null | Provider-normalized cost if available |
| `attempt` | integer | 1-based attempt index |

### StageError

| Field | Type | Description |
|-------|------|-------------|
| `code` | enum | See per-agent failure codes |
| `message` | string | Safe, non-secret summary |
| `retryable` | boolean | Whether a bounded retry is allowed |
| `details` | object \| null | Structured non-secret context |

---

## Extractor contract

### ExtractionRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | string | yes | |
| `shipment_id` | string | yes | |
| `document_id` | string | yes | |
| `customer_id` | string | yes | |
| `document_ref` | object | yes | Content handle (URI, storage key, or bytes hash) — **not** raw secrets |
| `document_type` | string \| null | no | Hint (e.g. `BILL_OF_LADING`, `INVOICE`); null = detect |
| `required_fields` | string[] | yes | Field names that must appear in the result (as `KNOWN`/`UNKNOWN`/`MISSING`/`AMBIGUOUS`) |
| `locale` | string \| null | no | |
| `timeout_ms` | integer | yes | Hard deadline for the extraction attempt budget |
| `correlation` | object \| null | no | Extra trace baggage |

### ExtractedField

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Canonical field name |
| `value` | any \| null | yes | Typed value or `null` per `presence` |
| `value_type` | string | yes | Declared type (`string`, `number`, `date`, `money`, …) |
| `presence` | FieldPresence | yes | `KNOWN` \| `UNKNOWN` \| `MISSING` \| `AMBIGUOUS` |
| `confidence` | number \| null | yes | See Confidence rules |
| `uncertainty` | UncertaintyFlag | yes | |
| `evidence` | Evidence[] | yes | May be empty only when `presence` ∈ {`UNKNOWN`,`MISSING`} and justified |
| `source_location` | object \| null | no | Convenience summary of primary evidence location |
| `warnings` | string[] | yes | Default `[]` |
| `candidates` | object[] \| null | no | For `AMBIGUOUS`: list of `{ value, confidence, evidence_ids }` |

### ExtractionResult

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | string | yes | |
| `document_id` | string | yes | |
| `status` | enum | yes | `SUCCEEDED` \| `PARTIAL` \| `FAILED` |
| `fields` | ExtractedField[] | yes | Must include every `required_fields` entry when status ≠ `FAILED` |
| `document_type_detected` | string \| null | no | |
| `warnings` | string[] | yes | |
| `errors` | StageError[] | yes | Non-empty when `FAILED` |
| `model` | ModelInvocationMetadata \| null | no | Null only for fully non-LLM extractors |
| `completed_at` | string (ISO-8601) | yes | |

**Invariants**

1. No `KNOWN` field with `value = null`.
2. No non-`KNOWN` field with non-null `value`.
3. Every `KNOWN` field has at least one `Evidence` with `source_type ≠ NONE` unless an ADR explicitly allows derived fields.
4. Schema validation failure ⇒ do not pass raw model text downstream; emit `FAILED` or repaired `PARTIAL` with `uncertainty = SCHEMA_REPAIR`.

---

## Validator contract

### ValidationRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | string | yes | |
| `shipment_id` | string | yes | |
| `document_id` | string | yes | |
| `customer_id` | string | yes | |
| `extraction` | ExtractionResult | yes | Must be `SUCCEEDED` or `PARTIAL` |
| `ruleset_id` | string | yes | Customer rules version id |
| `ruleset_version` | string | yes | |
| `timeout_ms` | integer | yes | |
| `correlation` | object \| null | no | |

### ValidationCheckStatus

| Value | Meaning |
|-------|---------|
| `MATCH` | Actual satisfies rule within policy |
| `MISMATCH` | Actual fails rule |
| `UNCERTAIN` | Insufficient information, confidence, or evidence to decide |

### ValidationCheck

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `check_id` | string | yes | Stable within run |
| `rule_id` | string | yes | From customer ruleset |
| `rule` | string | yes | Human-readable rule summary |
| `field_name` | string \| null | no | Primary field under test |
| `expected` | any \| null | no | Expected value/constraint summary |
| `actual` | any \| null | no | Actual extracted value (or null) |
| `result` | ValidationCheckStatus | yes | `MATCH` \| `MISMATCH` \| `UNCERTAIN` |
| `confidence` | number \| null | yes | Confidence in the check outcome |
| `evidence` | Evidence[] | yes | Grounding for the check (may reference extraction evidence ids) |
| `reason` | string | yes | Concise explanation |
| `deterministic` | boolean | yes | `true` if evaluated by deterministic engine |
| `severity` | enum | yes | `BLOCKING` \| `NON_BLOCKING` \| `INFORMATIONAL` |

### ValidationResult

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | string | yes | |
| `document_id` | string | yes | |
| `ruleset_id` | string | yes | |
| `ruleset_version` | string | yes | |
| `status` | enum | yes | `COMPLETED` \| `FAILED` |
| `checks` | ValidationCheck[] | yes | |
| `summary` | object | yes | Counts: `{ match, mismatch, uncertain, blocking_mismatch, blocking_uncertain }` |
| `warnings` | string[] | yes | |
| `errors` | StageError[] | yes | |
| `model` | ModelInvocationMetadata \| null | no | Present only if LLM-assisted checks ran |
| `completed_at` | string (ISO-8601) | yes | |

### Deterministic comparison rules (normative)

When a rule is marked deterministic and inputs are comparable:

| Situation | Required `result` |
|-----------|-------------------|
| Both sides present, equal under rule (case/normalize/tolerance as specified) | `MATCH` |
| Both sides present, not equal under rule | `MISMATCH` |
| Required field `presence` ∈ {`UNKNOWN`,`MISSING`,`AMBIGUOUS`} | `UNCERTAIN` (not `MISMATCH`, unless rule explicitly defines “must be present” as mismatch — then `MISMATCH` with reason `FIELD_ABSENT`) |
| Extraction field `confidence` below rule threshold | `UNCERTAIN` |
| Type-incompatible actual vs expected | `UNCERTAIN` or `MISMATCH` per rule; default `UNCERTAIN` if coercion unsafe |
| Ruleset load/parse failure | Stage `FAILED`; no silent `MATCH` |

LLM judgment **must not** override a completed deterministic `MATCH`/`MISMATCH` for the same `rule_id` in the same run. LLM may only produce checks for rules flagged `requires_judgment = true`.

---

## Router contract

### RoutingRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | string | yes | |
| `shipment_id` | string | yes | |
| `document_id` | string | yes | |
| `customer_id` | string | yes | |
| `extraction` | ExtractionResult | yes | |
| `validation` | ValidationResult | yes | Must be `COMPLETED` for normal routing; see fail-safe if `FAILED` |
| `policy_id` | string | yes | Routing policy version |
| `policy_version` | string | yes | |
| `timeout_ms` | integer | yes | |
| `correlation` | object \| null | no | |

### Decision

| Value | Meaning |
|-------|---------|
| `AUTO_APPROVE` | Safe to proceed without human touch under policy |
| `HUMAN_REVIEW` | Analyst must review before proceeding |
| `AMENDMENT_REQUEST` | Shipper should correct / resubmit |

### DecisionResult

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | string | yes | |
| `document_id` | string | yes | |
| `decision` | Decision | yes | |
| `reasons` | string[] | yes | Ordered, policy-grounded reasons |
| `triggering_check_ids` | string[] | yes | Validation checks that drove the decision |
| `policy_id` | string | yes | |
| `policy_version` | string | yes | |
| `confidence` | number \| null | yes | Confidence in the routing decision itself |
| `safety_constraints_applied` | string[] | yes | IDs of hard rules that fired (may be empty) |
| `llm_rationale` | string \| null | no | Optional narrative; **never** sole authority for `AUTO_APPROVE` |
| `model` | ModelInvocationMetadata \| null | no | |
| `completed_at` | string (ISO-8601) | yes | |
| `errors` | StageError[] | yes | |

### Decision relationship (normative safety)

Deterministic safety constraints **outrank** any LLM rationale.

| Condition | Required decision (minimum severity) |
|-----------|--------------------------------------|
| Validation `status = FAILED` | `HUMAN_REVIEW` (or safe halt; never `AUTO_APPROVE`) |
| Any `BLOCKING` check = `MISMATCH` | `AMENDMENT_REQUEST` or `HUMAN_REVIEW` per policy; never `AUTO_APPROVE` |
| Any `BLOCKING` check = `UNCERTAIN` | `HUMAN_REVIEW` (default) or `AMENDMENT_REQUEST` if policy maps absence→amendment; never `AUTO_APPROVE` |
| Extraction `status = FAILED` | `HUMAN_REVIEW` |
| Any required field `presence` ≠ `KNOWN` and field is policy-critical | Not `AUTO_APPROVE` |
| Router timeout / malformed output / exhausted retries | `HUMAN_REVIEW` |
| All blocking checks `MATCH`, no critical uncertainty, confidence ≥ policy threshold | `AUTO_APPROVE` **allowed** |
| LLM suggests `AUTO_APPROVE` but a safety constraint fires | Constraint wins; log override |

**Hard rule:** Never treat uncertainty, parse failure, or missing evidence as `AUTO_APPROVE`.

---

## Schema enforcement

Before any stage output crosses a trust boundary:

1. Parse into the typed contract.
2. Validate enums, nullability, and invariants above.
3. On failure: classify as malformed output; apply bounded retry only if `retryable`; otherwise fail safe.
4. Persist/reject — do not forward free-form model prose as a stage result.

Concrete schema IDL (JSON Schema / Protobuf / Pydantic / etc.) is chosen in a later ADR; this document defines the semantic contract those schemas must encode.

---

## Versioning

- Contract document version tracks via git + ADR supersession.
- Runtime payloads should carry `contract_version` when implementation begins.
- Breaking changes require a new ADR and migration notes.

---

## Related requirements (traceability)

Aligns with: `REQ-EXT-*`, `REQ-VAL-*`, `REQ-ROUTER-*`, `REQ-AI-*`, `REQ-TEST-004`, `REQ-OBS-*` (see requirements inventory when present on the integration branch).

## Related documents

- [extractor.md](./extractor.md)
- [validator.md](./validator.md)
- [router.md](./router.md)
- [trust-model.md](./trust-model.md)
- [../evaluation/agent-evaluation.md](../evaluation/agent-evaluation.md)
