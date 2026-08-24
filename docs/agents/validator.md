# Agent: Validator

| Field | Value |
|-------|-------|
| Status | Implemented (Phase 5 evaluation + deterministic/judgment agent) |
| Owner | AI Systems Architect / QA Evaluation |
| Last updated | 2026-08-25 |
| Related ADR(s) | [ADR-0010](../decisions/0010-ai-agent-contracts-and-trust-model.md) |
| Related feature(s) | Part 1 document verification pipeline |
| Contract | [contracts.md](./contracts.md#validator-contract) |
| Runtime | `src/nova/agents/validator/` (`ValidatorAgent`) |
| Evaluation | [../evaluation/validator-evaluation.md](../evaluation/validator-evaluation.md) |

## 1. Purpose

Compare extracted fields to **customer-specific rules** and emit auditable checks with status `MATCH`, `MISMATCH`, or `UNCERTAIN`.

The Validator is the primary place for **deterministic** rule evaluation. LLM judgment is optional and narrowly scoped.

### Responsibilities

- Load and apply the customer ruleset (`ruleset_id` + `ruleset_version`).
- Emit one or more `ValidationCheck` records per applicable rule.
- Prefer deterministic evaluation for equality, presence, numeric tolerance, allow-lists, and similar crisp checks.
- Propagate extraction uncertainty into `UNCERTAIN` (or explicit absence `MISMATCH` when the rule says so).
- Preserve evidence and reasons for every check.
- Never upgrade uncertainty into `MATCH` to “be helpful.”

### Non-responsibilities

- Field extraction from documents (Extractor).
- Final disposition `AUTO_APPROVE` / `HUMAN_REVIEW` / `AMENDMENT_REQUEST` (Router).
- Editing customer rules in production without versioning.
- Inventing expected values not present in the ruleset.
- Overriding deterministic results with free-form LLM prose.

## 2. Inputs

See `ValidationRequest` in [contracts.md](./contracts.md#validationrequest).

**Preconditions**

- `extraction.status` is `SUCCEEDED` or `PARTIAL`.
- Ruleset version is resolvable for `customer_id`.
- `timeout_ms` set by orchestrator.

If extraction `FAILED`, orchestrator should skip normal validation or pass through to Router fail-safe — Validator must not invent a full `MATCH` suite.

## 3. Outputs

See `ValidationResult` and `ValidationCheck` in [contracts.md](./contracts.md#validator-contract).

| Outcome | When |
|---------|------|
| `COMPLETED` | Checks produced for applicable rules (may include UNCERTAIN/MISMATCH) |
| `FAILED` | Ruleset unavailable, engine crash, timeout exhausted, unrecoverable error |

## 4. Behavior

### Deterministic path (default)

1. For each applicable rule, bind `expected` from ruleset and `actual` from extraction.
2. Apply documented comparison (normalize per rule: case fold, whitespace, date parse, money tolerance, etc.).
3. Assign `MATCH` / `MISMATCH` / `UNCERTAIN` per [deterministic comparison rules](./contracts.md#deterministic-comparison-rules-normative).
4. Set `deterministic = true`.

### Judgment path (optional, explicit)

1. Only for rules flagged `requires_judgment = true`.
2. LLM may propose a check outcome with reason and confidence.
3. Schema-validate the proposal.
4. Still cannot emit `MATCH` when inputs are `UNKNOWN`/`MISSING`/`AMBIGUOUS` unless the rule explicitly defines that semantics (default remains `UNCERTAIN`).
5. Set `deterministic = false` and record `ModelInvocationMetadata`.

### Obvious comparison examples

| Rule kind | Example | Result |
|-----------|---------|--------|
| Exact string (normalized) | Shipper name equals allow-list entry | `MATCH` / `MISMATCH` |
| Required presence | BL number must be present | `MISSING` → `MISMATCH` (if rule = must-present) or `UNCERTAIN` (if rule = compare-when-present) |
| Numeric tolerance | Weight within ±0.5% | Inside → `MATCH`; outside → `MISMATCH`; non-numeric actual → `UNCERTAIN` |
| Low extraction confidence | Confidence below threshold | `UNCERTAIN` even if strings equal |
| Ambiguous extraction | `presence = AMBIGUOUS` | `UNCERTAIN` |

## 5. Dependencies

| Direction | Component |
|-----------|-----------|
| Upstream | Extractor (`ExtractionResult`) |
| Downstream | Router (`ValidationResult`) |
| External | Customer rules store; optional LLM for judgment rules |

## 6. Failure modes

| Failure | Detection | Handling |
|---------|-----------|----------|
| Ruleset missing / corrupt | Load errors | `FAILED`; Router fail-safe |
| Timeout | Exceeds `timeout_ms` | Default `FAILED` (do not invent MATCH for unchecked rules) |
| Type coercion unsafe | Parse errors | Check `UNCERTAIN` |
| LLM judgment malformed | Schema fail | Bounded retry; else check `UNCERTAIN` |
| Extraction critical fields absent | Presence flags | Per-rule `UNCERTAIN`/`MISMATCH`; never blanket `MATCH` |

**Default timeout:** recommended orchestrator default **30_000 ms** for Part 1 deterministic-heavy validation (configurable).

**Retry policy:** Deterministic engine: **0** retries for logic errors; **1** retry for transient ruleset store I/O. LLM judgment: max **2** retries for malformed/transient errors. Never retry “into” a `MATCH` after uncertainty.

## 7. Security and data handling

- Rules and field values may contain commercial sensitive data — treat as sensitive.
- Do not log full rulesets with secrets; log `rule_id` + outcome.
- Validate LLM judgment output before use.

## 8. Testing

- Golden / synthetic fixtures: `fixtures/evaluation/validator/`
- Safety invariants: `tests/agents/validator/test_safety_invariants.py`
- Failure injection: `tests/failure/validator/`
- See [../testing/validator-evaluation.md](../testing/validator-evaluation.md)

## 9. Evaluation

- Harness: `src/nova/evaluation/validator/`
- Runner: `python scripts/run_validator_eval.py`
- Metrics + reports: [../evaluation/validator-evaluation.md](../evaluation/validator-evaluation.md)
- Critical gate: **unsafe MATCH count = 0**

## 10. Observability

- `run_id`, stage=`validator`, ruleset ids/versions
- Summary counts (match/mismatch/uncertain)
- Per-check `rule_id`, `outcome`, `deterministic`
- Model metadata when judgment used
- Latency and error codes (no sensitive document bodies)

## 11. Known limitations

- Rules DSL remains expression-dict based (future ADR for storage format).
- Cross-document consistency is Part 2 (`related_extractions` reserved).
- Live vendor LLM adapters not required for CI (MockLLM default).

## 12. Change history

| Date | Change | Author |
|------|--------|--------|
| 2026-08-25 | Initial contract and agent governance doc | AI Systems Architect |
| 2026-08-25 | Runtime Validator + evaluation/failure harness | QA / AI Evaluation |
