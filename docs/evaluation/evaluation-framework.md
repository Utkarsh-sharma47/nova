# Evaluation framework

Architecture for measuring Nova’s **AI quality and operational safety**. Complements [philosophy.md](./philosophy.md) and the [test strategy](../testing/test-strategy.md).

**Out of scope:** implementing the harness, labeling gold files, or shipping agents.

---

## Purpose

Evaluation answers: *Is the multi-agent pipeline operationally useful and safe on curated documents?*

It does **not** replace unit, contract, integration, or failure tests. Those prove deterministic correctness; evaluation measures probabilistic behavior under labeled conditions.

---

## Evaluation objects

| Object | What is scored |
|--------|----------------|
| Extractor | Field values, missing-field behavior, confidence, evidence |
| Validator | `MATCH` / `MISMATCH` / `UNCERTAIN` agreement with gold |
| Router | `AUTO_APPROVE` / `HUMAN_REVIEW` / `AMENDMENT_REQUEST` agreement + safety |
| Pipeline (optional rollup) | End-to-end disposition given gold stage labels or joint labels |
| NL query (later) | Groundedness and refusal on unknown |

Part 1 priority: Extractor, Validator, Router. NL query evaluation lands with query features.

---

## Process

```text
Labeled dataset (pinned)
    → run pipeline or stage under pinned model/prompt/policy versions
    → score with defined metrics
    → store report artifact (versions + scores + slice breakdowns)
    → compare to prior baseline / regression suite
    → gate release claims (human + policy)
```

1. **Select dataset slice** — see [datasets.md](./datasets.md).
2. **Pin versions** — model IDs, prompts, decoding, rule packs, router policy.
3. **Execute** — offline harness (to be implemented in Phase 5+).
4. **Score** — metrics in [metrics.md](./metrics.md); thresholds are calibration targets until baselines exist.
5. **Archive** — immutable report for audits (`REQ-SUBMISSION-002` evidence path).
6. **Decide** — regressions follow [regression-policy.md](./regression-policy.md).

---

## Dimensions by agent

### Extractor

| Dimension | Intent |
|-----------|--------|
| Field extraction accuracy | Agreement of extracted values with gold (normalized comparison rules TBD per field type) |
| Missing-field detection | Correctly flags fields that are absent vs inventing values |
| Confidence calibration | Confidence ranks correctness; over-confidence on wrong values is penalized |
| Evidence correctness | Evidence points at supporting document region/snippet for the claimed value |

### Validator

| Dimension | Intent |
|-----------|--------|
| MATCH accuracy | Gold MATCH predicted as MATCH |
| MISMATCH accuracy | Gold MISMATCH predicted as MISMATCH (with usable reasons) |
| UNCERTAIN accuracy | Gold UNCERTAIN predicted as UNCERTAIN — not coerced to MATCH |

Slice metrics by rule family when rule packs exist.

### Router

| Dimension | Intent |
|-----------|--------|
| AUTO_APPROVE precision | Of predicted AUTO_APPROVE, how many are gold-safe approvals (**critical**) |
| HUMAN_REVIEW recall | Of cases that should be reviewed, how many are routed to HUMAN_REVIEW |
| AMENDMENT_REQUEST correctness | Agreement with gold amendment cases (and that wrong values are not auto-approved) |

**Safety bar:** minimize false AUTO_APPROVE even if HUMAN_REVIEW rate rises. Over-routing to humans is preferable to silent approval of risk.

---

## Threshold policy

**Do not invent final numeric thresholds in this phase.**

All pass/fail cutoffs are **calibration targets** to be established from the evaluation dataset once:

- Gold labels exist for required slices (clean + messy minimum per `REQ-EXT-005`)
- A baseline run is recorded with pinned versions
- Stakeholders agree which metrics are release-blocking vs informational

Document calibrated thresholds in a later ADR or ops/evaluation update — never silently in a prompt.

---

## Report requirements

Every evaluation report must include:

- Dataset ID + revision
- Model / prompt / policy / rule-pack versions
- Metric table with slice breakdowns (at least clean vs messy)
- False AUTO_APPROVE count/rate when Router is in scope
- Latency and cost **if measured** (secondary; see [performance testing](../testing/performance-testing.md))
- Limitations (sample size, label uncertainty, provider variance)

Never fabricate scores. If a run failed, say so.

---

## Separation from CI unit tests

| | Unit / contract CI | Evaluation |
|--|--------------------|------------|
| LLM calls | No (except rare recorded stubs) | Yes, as designed |
| Flakiness tolerance | None | Controlled; variance reported |
| PR blocking | Always when suite exists | Only when explicitly gated |
| Purpose | Correctness of code | Quality & safety of behavior |

---

## Implementation status

| Item | Status |
|------|--------|
| Framework (this doc) | Documented |
| Metrics definitions | [metrics.md](./metrics.md) |
| Dataset categories | [datasets.md](./datasets.md) |
| Regression policy | [regression-policy.md](./regression-policy.md) |
| Harness code / gold files | Not implemented |

---

## Related requirements

- `REQ-EXT-005` — clean + messy samples
- `REQ-EXT-003` / `REQ-EXT-004` — confidence + evidence
- `REQ-VAL-002`–`004` — MATCH / MISMATCH / UNCERTAIN
- `REQ-ROUTER-001`–`005` — dispositions + fail-safe
- `REQ-SUBMISSION-002` — reproducible evaluation evidence
- `REQ-AI-004` (when inventoried) — messy/ambiguous handling without false certainty

---

## Related documents

- [philosophy.md](./philosophy.md)
- [test strategy](../testing/test-strategy.md)
- [agents](../agents/)
- [audits](../audits/)
