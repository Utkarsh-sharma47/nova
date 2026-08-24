# Evaluation philosophy

## Purpose

Extraction, ambiguity handling, and NL query quality are probabilistic. Evaluation measures whether Nova is **operationally useful and safe**, not whether a single prompt “looks good.”

## Part 1 eval objects

- **Clean sample** — well-formed document; expect high-confidence extraction and stable validation/routing.
- **Messy sample** — poor layout/noise/ambiguity; expect calibrated confidence, UNCERTAIN and/or HUMAN_REVIEW rather than false AUTO_APPROVE.
- **Adversarial / failure cases** — missing pages, wrong doc type, contradictory fields (as fixtures grow).

## Metrics (initial)

| Area | Example measures |
|------|------------------|
| Extraction | Field-level precision/recall vs labeled gold; calibration of confidence |
| Validation | Agreement with labeled MATCH/MISMATCH/UNCERTAIN |
| Routing | Agreement with labeled disposition; **false AUTO_APPROVE rate** (critical) |
| NL query | Groundedness; refusal on unknown |
| Ops | Latency per run; token/cost per run |

## Safety bar

A system that auto-approves incorrectly is worse than one that over-routes to HUMAN_REVIEW. Eval gates should prioritize **false AUTO_APPROVE** minimization.

## Process

1. Label gold outputs for fixtures.
2. Run eval command (to be introduced in implementation phases).
3. Store report artifacts with model/prompt versions.
4. Regressions block release/demo claims.

## Phase 1 note

No eval harness code yet — only the philosophy and requirements (`REQ-EXT-005`, `REQ-SUBMISSION-002`).
