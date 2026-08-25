# Failure testing

Failure tests prove Nova **fails safe**: errors, partial results, and infrastructure faults must not become silent `AUTO_APPROVE` or invented field values.

**Out of scope:** implementing resilience code or chaos tooling yet.

---

## Principles

1. Every critical failure mode has at least one automated test when the corresponding code exists.
2. Default degrade path is **HUMAN_REVIEW**, safe halt, or structured error — never optimistic approval.
3. Retries are **bounded**; exhaustion is an explicit terminal failure.
4. Partial processing is visible in run status and persisted records.
5. Failure tests are deterministic (injected faults / fakes), not “hope the provider flakes.”

---

## Failure catalog

### LLM / model provider

| Scenario | Expected system behavior (intent) | Primary layers |
|----------|-----------------------------------|----------------|
| LLM timeout | Stage fails or returns structured error; no invented fields; no AUTO_APPROVE | Failure, integration |
| LLM malformed output | Schema validation rejects; bounded repair/retry if designed; else UNCERTAIN/error path | Unit (parser), contract, failure |
| LLM unavailable | Circuit/open error; run marked failed or HUMAN_REVIEW per policy | Failure, integration |
| Rate limiting | Backoff within budget; on exhaustion, explicit failure | Unit (backoff), failure |

### Data / storage

| Scenario | Expected system behavior (intent) | Primary layers |
|----------|-----------------------------------|----------------|
| Database unavailable | API/run fails clearly; no partial silent success claiming persistence | Failure, integration |
| Duplicate document | Idempotent handling: same logical submission does not double-apply conflicting decisions | Integration, unit (keys) |

### Document input

| Scenario | Expected system behavior (intent) | Primary layers |
|----------|-----------------------------------|----------------|
| Corrupt file | Reject or fail extraction with structured error; no crash of whole service | Failure, E2E smoke |
| Unsupported file | Reject with clear unsupported-type error before/at ingestion | Unit, contract, failure |
| Missing field (business) | Extractor marks missing; Validator/Router treat as MISMATCH or UNCERTAIN per rules — not MATCH-by-omission | Unit, evaluation fixtures |
| OCR corruption (as input quality) | Low confidence / UNCERTAIN / HUMAN_REVIEW rather than false certainty | Evaluation + failure where parser breaks |

### Rules and processing

| Scenario | Expected system behavior (intent) | Primary layers |
|----------|-----------------------------------|----------------|
| Invalid customer rule | Rule pack validation fails before applying; structured error; no silent skip-to-approve | Contract, failure |
| Partial processing | Run status shows which stages completed; downstream does not assume full success | Integration, failure |
| Retry exhaustion | Terminal failure after max attempts; metrics/logs record attempt count; no infinite loop | Unit, failure |

---

## Router fail-safe matrix

| Upstream condition | Forbidden outcome | Required direction |
|--------------------|-------------------|--------------------|
| Extractor hard failure | `AUTO_APPROVE` | Error halt or `HUMAN_REVIEW` |
| Validator UNCERTAIN present (policy-dependent) | Silent `AUTO_APPROVE` without policy satisfaction | `HUMAN_REVIEW` or `AMENDMENT_REQUEST` as policy dictates |
| Malformed agent payload | `AUTO_APPROVE` | Reject / HUMAN_REVIEW |
| Persistence failure after decision compute | Claiming durable AUTO_APPROVE without store | Error; retry store or mark incomplete |
| Missing policy version / invalid rules | `AUTO_APPROVE` | Fail closed |

This matrix must be covered by automated failure tests once Router exists (`REQ-ROUTER-005`).

---

## Injection approach (planned)

Prefer controllable seams:

- Fake LLM client returning timeout, 429, 5xx, garbage JSON, truncated JSON
- Fake DB repository raising unavailable / constraint errors
- Fixture files: truncated PDF/bytes, wrong MIME, empty file
- Rule packs: schema-invalid YAML/JSON, unknown operators, contradictory rules

Avoid relying on live provider outages for CI.

---

## Observability expectations in failure tests

When observability exists, failure tests should assert (at least one of):

- Correlated run ID on error logs
- Stage name and error class recorded
- Retry count and final status
- No secret material in logged payloads

---

## Relationship to evaluation

| Concern | Failure tests | Evaluation |
|---------|---------------|------------|
| Provider down | Yes | No |
| Model returns valid but wrong field | No (unless contract) | Yes |
| Ambiguous document → UNCERTAIN | Optional golden | Yes (messy/ambiguous sets) |
| Adversarial prompt injection in document text | Optional security/failure fixture | Adversarial dataset category |

---

## CI

Critical-path failure tests are **required** in PR CI when implemented. Broader chaos/soak belongs in scheduled jobs.

---

## Related

- [test-strategy.md](./test-strategy.md)
- [contract-testing.md](./contract-testing.md)
- [evaluation datasets](../evaluation/datasets.md) (adversarial / messy categories)
- Requirements: REQ-EXT-006, REQ-ROUTER-005, REQ-OBS-*, reliability NFRs when documented
