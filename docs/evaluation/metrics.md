# Evaluation metrics

Metric definitions for Nova AI evaluation. **No final numeric thresholds** are set here.

All pass/fail cutoffs are **calibration targets** to be established from labeled evaluation datasets and recorded later (ADR or evaluation ops update).

---

## Conventions

| Term | Meaning |
|------|---------|
| Gold | Human-labeled expected value or outcome |
| Pred | System prediction under pinned versions |
| Slice | Subset by dataset category (clean, messy, …) |
| Calibration target | Provisional bar derived from baseline runs — not yet a formal SLO |

Report metrics **overall and per slice**. Always report sample size `n`.

Normalization rules for field comparison (case folding, whitespace, numeric tolerance, synonym tables) will be defined with the harness — until then, treat comparison policy as an explicit report field.

---

## Extractor metrics

| Metric | Definition (intent) | Notes |
|--------|---------------------|-------|
| Field extraction accuracy | Agreement rate between pred and gold values over required fields (exact or normalized match per field policy) | Also report per-field accuracy |
| Field precision / recall (optional micro/macro) | When extraction is framed as detecting present fields/values | Useful for sparse docs |
| Missing-field detection rate | Among gold-missing required fields, fraction correctly marked missing / unavailable | Penalize invented values separately |
| Hallucinated-field rate | Among fields gold-absent, fraction where system emits a concrete value | Safety-critical companion to accuracy |
| Confidence calibration | Reliability of confidence vs correctness (e.g. expected calibration error, or accuracy by confidence bucket) | Over-confidence on errors is a first-class failure mode |
| Evidence correctness rate | Among extracted values with gold evidence spans (when labeled), fraction whose evidence supports the claimed value | Evidence pointing at unrelated text counts as incorrect |
| Evidence presence rate | Fraction of extracted values that include evidence when policy requires it | Contract tests also enforce schema presence |

**Calibration targets (to establish later):** minimum field accuracy on clean slice; maximum hallucinated-field rate; maximum ECE / over-confidence on messy slice — values TBD from dataset.

---

## Validator metrics

| Metric | Definition (intent) | Notes |
|--------|---------------------|-------|
| MATCH accuracy | Recall/precision for class MATCH (report both; state primary) | Do not optimize MATCH by collapsing UNCERTAIN |
| MISMATCH accuracy | Recall/precision for class MISMATCH | Reasons quality may be audited qualitatively |
| UNCERTAIN accuracy | Recall/precision for class UNCERTAIN | Punish UNCERTAIN→MATCH conversions hard in safety review |
| 3-way agreement rate | Fraction of checks where pred class equals gold class | Macro-F1 optional for imbalance |
| Dangerous upgrade rate | Fraction of gold UNCERTAIN or MISMATCH predicted as MATCH | Release-critical companion metric |

**Calibration targets (to establish later):** minimum per-class accuracy; maximum dangerous upgrade rate — TBD from dataset.

---

## Router metrics

| Metric | Definition (intent) | Notes |
|--------|---------------------|-------|
| AUTO_APPROVE precision | `TP_auto / (TP_auto + FP_auto)` where positive class is AUTO_APPROVE | **Primary safety metric** — false AUTO_APPROVE is worst outcome |
| AUTO_APPROVE recall | Optional; lower recall is acceptable if precision is protected | Over-routing to humans preferred |
| HUMAN_REVIEW recall | Among gold HUMAN_REVIEW (and policy-equivalent must-review cases), fraction predicted HUMAN_REVIEW | May include gold cases labeled “must not auto-approve” |
| HUMAN_REVIEW precision | Optional companion | |
| AMENDMENT_REQUEST correctness | Agreement rate on gold amendment cases (precision/recall for that class) | Ensure incorrect values are not AUTO_APPROVE |
| 3-way disposition agreement | Pred disposition equals gold | Report with confusion matrix |
| False AUTO_APPROVE rate | `FP_auto / n` or `/ n_non_auto_gold` — define clearly in each report | Must appear on every Router-inclusive report |

**Calibration targets (Router decision eval, dataset `nova-decision-eval` rev `2026-08-25.r1`):**

| Metric | Target | Scope |
|--------|--------|-------|
| False AUTO_APPROVE rate | **0.0** | Regression tag set |
| AUTO_APPROVE precision | 1.0 when any AUTO_APPROVE predicted | Same |

These are **evaluation-policy calibration / regression gates**, not production SLOs
or claims about unseen customer traffic. See [decision-evaluation.md](./decision-evaluation.md)
and [regression-policy.md](./regression-policy.md). Until broader calibration exists,
any false AUTO_APPROVE on the regression set is a **blocking investigation**.

---

## Pipeline rollup (optional)

| Metric | Intent |
|--------|--------|
| End-to-end disposition agreement | Gold final disposition vs pred when joint labels exist |
| Safe-path rate | Pred is “safe” relative to gold (e.g. equal, or stricter toward human/amendment) | Define “stricter” mapping explicitly in reports |

---

## Operational metrics (secondary in eval reports)

May be copied from [performance testing](../testing/performance-testing.md):

- Document processing latency
- LLM latency
- Cost per document

These do not replace quality/safety metrics.

---

## What not to do

- Do not invent scores or thresholds without runs.
- Do not average away false AUTO_APPROVE inside a single “accuracy” number.
- Do not tune prompts against the full regression set without a holdout/calibration split.
- Do not claim production readiness from clean-slice metrics alone.

---

## Related

- [evaluation-framework.md](./evaluation-framework.md)
- [datasets.md](./datasets.md)
- [regression-policy.md](./regression-policy.md)
- [philosophy.md](./philosophy.md)
