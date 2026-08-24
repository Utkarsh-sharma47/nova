# Contract testing

Contract tests lock the **typed boundaries** between Nova pipeline stages and external interfaces. They run in PR CI whenever application schemas exist.

**Out of scope:** implementing agents or choosing schema libraries (ADR later).

---

## Purpose

1. Prevent silent breakage when Extractor, Validator, Router, API, or persistence shapes change.
2. Ensure confidence, evidence, and uncertainty fields cannot be dropped “for convenience.”
3. Guarantee fail-safe error shapes exist (so routers cannot invent AUTO_APPROVE from empty failures).
4. Preserve Part 2 extension points in schemas (e.g. multi-document context hooks) without implementing Part 2.

---

## What is a contract test

A contract test asserts that:

- A representative payload **validates** against the published schema/type, and
- Required semantic invariants hold (enums, required fields, non-empty reasons where mandated), and
- **Incompatible** payloads are rejected.

Contract tests do **not** call live LLMs and do **not** score accuracy.

---

## Contract surfaces

### Extractor

| Surface | Must cover |
|---------|------------|
| Input | Document reference, document type (or unknown), run/shipment IDs, content handle |
| Success output | Typed field map; per-field confidence; per-field evidence/grounding; model/prompt version metadata when available |
| Partial / missing | Explicit missing-field representation (not silently omitted as “success with invention”) |
| Failure output | Structured error; isolation metadata; no invented field values |

**Invariants**

- Every returned field value has confidence (or explicit null + reason).
- Evidence is present for extracted values intended for audit/review.
- Unknown/unavailable values are marked as such — never fabricated.

### Validator

| Surface | Must cover |
|---------|------------|
| Input | Extractor-shaped fields + customer rule pack reference/version |
| Outcome enum | `MATCH`, `MISMATCH`, `UNCERTAIN` only (no silent synonyms) |
| Per-check record | Rule ID, outcome, reason, inputs referenced |
| Aggregate | Document/run-level summary compatible with Router input |

**Invariants**

- `UNCERTAIN` is a first-class outcome (not coerced to MATCH).
- MISMATCH and UNCERTAIN carry human-readable reasons suitable for review/amendment.
- Invalid rule packs produce structured validation errors (see failure tests).

### Router

| Surface | Must cover |
|---------|------------|
| Input | Validation outcomes + policy version + confidence/evidence summaries as required by policy |
| Decision enum | `AUTO_APPROVE`, `HUMAN_REVIEW`, `AMENDMENT_REQUEST` |
| Rationale | Machine-readable reasons + policy references |
| Failure / degrade | Explicit non-AUTO_APPROVE path when inputs incomplete or upstream failed |

**Invariants**

- Schema forbids implying AUTO_APPROVE without required policy fields.
- Error dispositions are expressible without overloading MATCH semantics.

### Persistence and API

| Surface | Must cover |
|---------|------------|
| Submission / run create | IDs, document refs, status transitions |
| Read models | Extraction, validation, decision records reconstructible for audit |
| Query | Request/response shapes; grounded-answer vs explicit refusal discriminators |
| Idempotency | Duplicate submission keys / document fingerprints |

### Part 2 readiness (schema only)

Contracts should allow, without requiring Part 1 callers to use them:

- Multiple documents per shipment
- Optional multi-document validation context
- Ingestion source discriminator (upload vs future email/file triggers)

Do not implement Part 2 adapters in Part 1.

---

## Fixture catalog (planned)

Maintain golden JSON (or equivalent) fixtures under the future test tree, for example:

| Fixture family | Intent |
|----------------|--------|
| `extractor/success_clean` | Full fields + confidence + evidence |
| `extractor/missing_fields` | Required fields explicitly missing |
| `extractor/error_timeout` | Structured failure |
| `validator/match` | All checks MATCH |
| `validator/mismatch` | At least one MISMATCH with reasons |
| `validator/uncertain` | UNCERTAIN from low confidence / weak evidence |
| `router/auto_approve` | Legal AUTO_APPROVE under policy |
| `router/human_review` | HUMAN_REVIEW |
| `router/amendment_request` | AMENDMENT_REQUEST |
| `router/fail_safe` | Upstream failure → not AUTO_APPROVE |

Exact paths and tooling land with implementation phases.

---

## Compatibility rules

1. **Additive changes** (optional fields) preferred over breaking renames.
2. Breaking contract changes require ADR + migration notes + dual-read period when persistence is involved.
3. Consumer stages must contract-test against **producer** fixtures (Validator consumes Extractor goldens; Router consumes Validator goldens).
4. Prompt-only changes that alter output shape still require contract updates — prompts are not a substitute for schemas.

---

## CI expectations

When schemas exist:

- Contract suite is **required** on every PR.
- Generated clients (if any) must regenerate and pass in the same change.
- Do not disable contract tests to land a prompt experiment.

Until schemas exist: document contracts in `docs/agents/` / ADRs; this catalog remains the checklist.

---

## Related

- [test-strategy.md](./test-strategy.md)
- [failure-testing.md](./failure-testing.md)
- [architecture rules](../ai-development/architecture-rules.md)
- Requirements: REQ-EXT-003/004, REQ-VAL-002–004, REQ-ROUTER-001–005, REQ-DATA-*, REQ-AI-*
