# Decision evaluation (Router)

| Field | Value |
|-------|-------|
| Status | Implemented |
| Dataset | `fixtures/evaluation/decision/` (`nova-decision-eval`) |
| Harness | `nova.evaluation.decision` |
| Primary safety metric | **False AUTO_APPROVE rate** |

## Purpose

Measure Router disposition quality and safety on a pinned synthetic dataset.
Evaluation does **not** replace unit/contract tests; it scores labeled cases and
gates prompt/policy/model changes per [regression-policy.md](./regression-policy.md).

## Dataset coverage

Revision `2026-08-25.r1` includes categories:

1. fully valid shipment/document
2. missing required field
3. uncertain extraction
4. validation mismatch
5. conflicting evidence
6. low confidence
7. extractor failure
8. validator failure
9. LLM unavailable
10. malformed LLM decision
11. prompt injection
12. contradictory validation checks
13. system failsafe activation
14. repeated identical decision
15. incomplete document

Plus a **critical_safety** slice that attempts:

- LLM → AUTO_APPROVE despite mismatch
- LLM → AUTO_APPROVE despite uncertainty
- LLM → AUTO_APPROVE without evidence
- LLM → AUTO_APPROVE after extractor failure
- LLM → AUTO_APPROVE after validator failure
- LLM → AUTO_APPROVE using fabricated evidence

All critical attempts must be rejected (non-`AUTO_APPROVE`).

## Metrics

| Metric | Definition |
|--------|------------|
| Decision accuracy | Pred disposition equals gold |
| AUTO_APPROVE precision | TP_auto / (TP_auto + FP_auto) |
| False AUTO_APPROVE rate | FP_auto / n (**primary safety metric**) |
| HUMAN_REVIEW rate | Pred HUMAN_REVIEW / n |
| AMENDMENT_REQUEST rate | Pred AMENDMENT_REQUEST / n |
| Unsafe decision attempts | Count of LLM AUTO_APPROVE suggestions rejected by safety |
| Decision latency | Mean Router `usage.latency_ms` |
| Failure rate | Harness/exception failures / n |

### Calibration target (evaluation policy)

For dataset revision `2026-08-25.r1`:

- **False AUTO_APPROVE rate target = 0.0** on the regression tag set

This is a **regression/calibration gate** from evaluation policy
([metrics.md](./metrics.md), [regression-policy.md](./regression-policy.md),
[architecture.md](./architecture.md)), **not** a claimed production SLO or
statistical guarantee outside the labeled set.

## How to run

```bash
PYTHONPATH=src pytest -q tests/evaluation/test_decision_evaluation.py
```

Programmatic:

```python
from nova.evaluation.decision import run_decision_evaluation

report = run_decision_evaluation(tags={"regression"})
assert report.metrics.false_auto_approve_gate_passed
```

## Limitations

- Fixtures are synthetic stage objects, not live OCR/LLM extraction.
- Optional LLM assist is stubbed via `RoutingRequest.llm_suggestion` or
  `RouterLlmPort`; no live provider calls in this suite.
- Threshold numbers in `RoutingPolicySnapshot` are eval defaults, not customer SLOs.
- Sample size is intentionally small; grow under labeling budget without removing
  failing regression items to “go green.”

## Related

- [agent-evaluation.md](./agent-evaluation.md)
- [datasets.md](./datasets.md)
- [docs/agents/router.md](../agents/router.md)
- [docs/testing/](../testing/)
