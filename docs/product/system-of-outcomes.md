# System of outcomes

Nova is judged by **operational outcomes**, not by the mere presence of three agents.

## Outcome chain

```text
Document received
  → Fields extracted with confidence + evidence
  → Rules applied → MATCH | MISMATCH | UNCERTAIN
  → Disposition → AUTO_APPROVE | HUMAN_REVIEW | AMENDMENT_REQUEST
  → Record persisted and queryable
  → Human attention spent only where risk remains
```

## Outcome definitions

| Outcome | Meaning | Success signal |
|---------|---------|----------------|
| **Correct extraction** | Required fields recovered for the document type | Eval on clean sample meets field contract |
| **Honest uncertainty** | Low confidence / weak evidence is visible | Messy sample does not produce false certainty |
| **Consistent validation** | Same customer rules → same class of results | Golden MATCH/MISMATCH/UNCERTAIN suite |
| **Safe routing** | Risk does not become silent AUTO_APPROVE | Failure + UNCERTAIN → HUMAN_REVIEW (or halt) |
| **Auditability** | Decision can be reconstructed | Persisted records + run traces |
| **Queryable operations** | Staff can retrieve history without inventing facts | API + grounded NL answers |
| **Reviewable UI** | Analysts can act on evidence | Minimal UI shows fields, confidence, evidence, outcomes |

## What Nova automates vs reserves for humans

| Automate (Part 1) | Reserve for humans |
|-------------------|--------------------|
| Field extraction proposals | Final judgment on low-confidence / UNCERTAIN cases |
| Deterministic rule checks | Policy edge cases and high-risk shipments |
| Suggested disposition under policy | Override when operational context demands |
| Persistence and retrieval | Part 2 approval before outbound send |

## Failure outcomes (must be first-class)

| Failure | Required system behavior |
|---------|--------------------------|
| Unreadable / corrupt input | Structured error; no AUTO_APPROVE |
| Extraction timeout / LLM error | Fail-safe disposition (HUMAN_REVIEW or halt) |
| Rules cannot be evaluated | UNCERTAIN → human path |
| NL query without supporting records | Refuse / say unknown |

## Part 2 outcomes (deferred)

- Email-native intake
- Multi-document consistency
- Drafted amendment communications
- Approved outbound sends

Part 1 only ensures these remain **possible** via extension points.
