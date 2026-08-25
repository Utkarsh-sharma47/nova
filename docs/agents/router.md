# Agent: Router

| Field | Value |
|-------|-------|
| Status | Implemented (Phase 6) |
| Owner | Decision and Routing Engineer |
| Last updated | 2026-08-25 |
| Related ADR(s) | [ADR-0010](../decisions/0010-ai-agent-contracts-and-trust-model.md) |
| Related feature(s) | Part 1 document verification pipeline; [router-decision-agent.md](../features/router-decision-agent.md) |
| Contract | [contracts.md](./contracts.md#router-contract) |
| Runtime | `src/nova/router/` (`RouterService`) |

## 1. Purpose

Map extraction + validation outcomes to a single disposition:

- `AUTO_APPROVE`
- `HUMAN_REVIEW`
- `AMENDMENT_REQUEST`

Routing is **policy-first**. LLM rationale, if any, is advisory and cannot bypass deterministic safety constraints.

### Responsibilities

- Apply versioned routing policy (`policy_id` + `policy_version`).
- Enforce hard safety constraints from [contracts.md](./contracts.md#decision-relationship-normative-safety).
- Produce `DecisionResult` with reasons and triggering check IDs.
- Fail safe to `HUMAN_REVIEW` (or non-approve halt) on errors/timeouts/malformed output.
- Record whether safety constraints overrode any model suggestion.

### Non-responsibilities

- Extracting fields or re-parsing documents.
- Re-evaluating customer rules (that is Validator’s job); Router consumes check results.
- Sending emails or amendment messages (Part 2 communication agents).
- Persisting records (orchestrator/persistence layer).
- Silently auto-approving when validation failed or uncertainty remains.

## 2. Inputs

See `RoutingRequest` in [contracts.md](./contracts.md#routingrequest).

**Preconditions**

- Extraction and validation objects are schema-valid.
- Policy version resolvable for customer.

## 3. Outputs

See `DecisionResult` in [contracts.md](./contracts.md#decisionresult).

Every run that reaches the Router must yield exactly one `decision` enum value (or an orchestrator-level safe halt that is operationally equivalent to not approving).

## 4. Behavior

### Relationship: validation → confidence → uncertainty → decision

```text
Validation checks + extraction presence/confidence
        │
        ▼
Deterministic safety constraints  ──(if fire)──► force HUMAN_REVIEW or AMENDMENT_REQUEST
        │ (none fire)
        ▼
Policy thresholds (confidence, blocking counts, customer overrides)
        │
        ▼
Optional LLM tie-break for gray-zone cases only
        │
        ▼
DecisionResult (AUTO_APPROVE only if still eligible)
```

| Signal | Effect on decision space |
|--------|---------------------------|
| Blocking `MISMATCH` | Disallow `AUTO_APPROVE`; prefer `AMENDMENT_REQUEST` or `HUMAN_REVIEW` per policy |
| Blocking `UNCERTAIN` | Disallow `AUTO_APPROVE`; default `HUMAN_REVIEW` |
| Low field confidence / non-KNOWN critical fields | Disallow `AUTO_APPROVE` |
| All blocking `MATCH`, confidence ≥ threshold | `AUTO_APPROVE` eligible |
| Stage/policy/LLM failure | `HUMAN_REVIEW` |

### Deterministic safety constraints (non-bypassable)

These run **before** any LLM suggestion is accepted:

1. `validation.status != COMPLETED` → not `AUTO_APPROVE`
2. Any blocking `MISMATCH` → not `AUTO_APPROVE`
3. Any blocking `UNCERTAIN` → not `AUTO_APPROVE`
4. Extraction `FAILED` → not `AUTO_APPROVE`
5. Malformed router output / timeout / exhausted retries → `HUMAN_REVIEW`
6. LLM-only rationale with empty `triggering_check_ids` for `AUTO_APPROVE` → reject; force `HUMAN_REVIEW`

Vague natural-language justification (“looks fine”) is insufficient for `AUTO_APPROVE`.

### Optional LLM assist

Allowed only to:

- Rank gray-zone cases between `HUMAN_REVIEW` and `AMENDMENT_REQUEST`
- Produce human-readable `llm_rationale` for auditors

Not allowed to:

- Create `AUTO_APPROVE` when constraints forbid it
- Invent validation outcomes that Validator did not emit

## 5. Dependencies

| Direction | Component |
|-----------|-----------|
| Upstream | Validator (`ValidationResult`), Extractor (`ExtractionResult`) |
| Downstream | Persistence, UI review queue, Part 2 communication triggers |
| External | Policy store; optional LLM |

## 6. Failure modes

| Failure | Detection | Handling |
|---------|-----------|----------|
| Policy missing | Load error | Safe halt / `HUMAN_REVIEW` |
| Timeout | Exceeds `timeout_ms` | `HUMAN_REVIEW` |
| Malformed LLM output | Schema fail | Bounded retry; then `HUMAN_REVIEW` |
| Conflicting signals | Constraint engine | Constraints win; log `safety_constraints_applied` |
| Empty validation checks when rules expected | Invariant check | `HUMAN_REVIEW` |

**Default timeout:** recommended orchestrator default **15_000 ms** (policy evaluation is primarily deterministic).

**Retry policy:** Deterministic policy: **0** logic retries. LLM assist: max **2** retries for transient/malformed. After exhaustion → `HUMAN_REVIEW`. Never retry toward `AUTO_APPROVE` after a constraint failure.

## 7. Security and data handling

- Decisions are audit-critical; persist policy versions and constraint IDs.
- Do not allow prompt injection in document text to alter disposition enums — enums must be schema-validated and constraint-checked post-model.
- Redact sensitive field values in rationale logs as required.

## 8. Testing

- Golden cases for all three decisions (`tests/agents/router/`, `tests/router/`)
- Constraint tests: uncertainty never yields `AUTO_APPROVE`
- Failure tests: timeout/malformed/failsafe → `HUMAN_REVIEW`
- Adversarial: LLM returns `AUTO_APPROVE` while blocking mismatch present → overridden
- Fixed decision regression dataset: `fixtures/evaluation/decision/` (tag `regression`)

## 9. Evaluation

Harness: [`docs/evaluation/decision-evaluation.md`](../evaluation/decision-evaluation.md)
(`nova.evaluation.decision`).

| Metric | Role |
|--------|------|
| Decision agreement vs labeled gold | Quality |
| **False `AUTO_APPROVE` rate** | **Primary safety bar** |
| AUTO_APPROVE precision | Safety companion |
| HUMAN_REVIEW / AMENDMENT_REQUEST rates | Routing mix |
| Unsafe LLM attempt count | Adversarial pressure |
| Decision latency / failure rate | Ops |

Over-routing to `HUMAN_REVIEW` is acceptable relative to false approve.

**Calibration target (dataset `nova-decision-eval` rev `2026-08-25.r1`):**
false AUTO_APPROVE rate **0.0** on the regression set — an evaluation-policy gate,
not a production SLO claim.

## 10. Observability

- `run_id`, stage=`router`, `decision`, policy ids/versions
- `safety_constraints_applied`
- `triggering_check_ids`
- Whether LLM assist ran and whether it was overridden (`llm_overridden`, `unsafe_llm_attempt`)
- Latency, errors, attempts
- `input_fingerprint` for deterministic replay

## 11. Known limitations

- Concrete threshold numbers are customer/policy-specific and calibrated via
  versioned `RoutingPolicySnapshot` (defaults: high=0.85, low=0.60).
- Human approval workflow UX is Part 2; Part 1 still emits `HUMAN_REVIEW` as a
  first-class decision.
- Live provider LLM assist is optional; Part 1 safety does not depend on it.
- Decision evaluation fixtures are synthetic stage payloads (not live OCR).

## 12. Change history

| Date | Change | Author |
|------|--------|--------|
| 2026-08-25 | Initial contract and agent governance doc | AI Systems Architect |
| 2026-08-25 | Phase 6 runtime: `RouterService`, failsafe, persistence | Decision and Routing Engineer |
| 2026-08-25 | Decision evaluation dataset + metrics harness | Safety and Evaluation Engineer |
