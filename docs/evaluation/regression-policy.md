# AI regression policy

**Mandatory rule:** every future prompt, model, decoding, rule-pack, or router-policy change that can alter Extractor, Validator, or Router behavior must be evaluated against a **fixed regression dataset** before release notes, demo claims, or “quality improved” statements.

This policy is documentation-only until the harness exists; the rule still binds contributors and AI coding agents.

---

## Why

Small prompt edits can raise clean-document accuracy while increasing false `AUTO_APPROVE` on messy or adversarial cases. Fixed regression evaluation is the only honest way to detect that tradeoff.

---

## Scope of changes requiring regression evaluation

| Change type | Regression eval required? |
|-------------|---------------------------|
| Prompt text for Extractor / Validator / Router | Yes |
| Model ID or provider swap for those agents | Yes |
| Decoding / temperature / tool settings affecting outputs | Yes |
| Router policy thresholds or disposition mapping | Yes |
| Customer rule DSL semantics affecting MATCH/MISMATCH/UNCERTAIN | Yes |
| Evidence or confidence post-processing that affects downstream decisions | Yes |
| Pure docs / typo fixes with no runtime effect | No |
| Unrelated UI CSS with no pipeline impact | No |
| Failure-handling timeouts that do not change success-path outputs | Failure tests; eval if success-path behavior can change |

If unsure, run the regression suite.

---

## Fixed regression dataset

1. A named dataset revision is designated **regression** (see [datasets.md](./datasets.md)).
2. Contents are pinned: items are not removed to silence failures.
3. Additions are allowed via a new dataset revision; compare reports across revisions explicitly.
4. Minimum category coverage must be preserved (clean, messy, missing, and disposition coverage as datasets grow).

---

## Required procedure

```text
1. Implement change on a feature branch
2. Run unit/contract/integration/failure suites (when they exist)
3. Run evaluation harness on the fixed regression dataset revision
4. Diff metrics vs last accepted baseline (same dataset revision when possible)
5. Investigate any new false AUTO_APPROVE or dangerous Validator upgrades
6. Record report artifact with versions
7. Only then claim improvement or cut a release/demo
```

### Blocking conditions (until numeric thresholds are calibrated)

Treat as **release-blocking investigations** (must resolve or explicitly accept with human sign-off):

- Any **new** false `AUTO_APPROVE` on the regression set versus baseline
- Any increase in hallucinated-field rate on missing-field / unknown slices
- Any systematic UNCERTAIN/MISMATCH → MATCH upgrade on gold non-MATCH checks
- Harness failure or incomplete run presented as success

Calibrated numeric gates will replace/extend this list after baseline measurement — see [metrics.md](./metrics.md).

---

## Baseline management

- **Accepted baseline:** last report signed off for a given dataset revision + production-intended versions.
- Challenger runs must cite baseline report ID.
- Prefer improving precision of AUTO_APPROVE and reducing hallucinations over chasing clean-slice accuracy alone.

---

## CI integration (planned)

| Stage | Behavior |
|-------|----------|
| PR | Optional/informational eval job when cost allows; never fake green |
| Pre-release / main quality claim | Required regression eval |
| Scheduled | Catch provider drift on pinned prompts |

Do not delete regression cases or weaken metrics to obtain a green job (`docs/ai-development/testing-rules.md`).

---

## Responsibilities

| Role | Duty |
|------|------|
| Author of prompt/model/policy change | Run (or request) regression eval; attach summary to PR |
| Reviewer | Verify dataset revision, versions, and false AUTO_APPROVE delta |
| AI coding agents | Never claim quality wins without eval evidence; never skip this policy |

---

## Exceptions

Temporary exceptions require **human** written approval in the PR (reason, expiry, residual risk). AI agents may not self-approve exceptions.

---

## Related

- [evaluation-framework.md](./evaluation-framework.md)
- [datasets.md](./datasets.md)
- [metrics.md](./metrics.md)
- [test strategy](../testing/test-strategy.md)
- [AGENTS.md](../../AGENTS.md)
- [testing rules](../ai-development/testing-rules.md)
