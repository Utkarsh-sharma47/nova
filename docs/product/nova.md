# Nova

## One-line definition

Nova is an **operational trade-document verification system**: a multi-agent pipeline that extracts fields from shipping documents, validates them against customer-specific rules, and routes each case to auto-approve, human review, or amendment request.

## What Nova is not

- Not a general chatbot
- Not a dashboard-only analytics toy
- Not a promise of fully autonomous settlement without human-in-the-loop controls

## Operational pipeline

```text
Document
  → ingestion
  → extraction
  → confidence / evidence
  → validation (customer rules)
  → routing (disposition)
  → persistence
  → query
  → minimal B2B UI
```

Agents (Extractor, Validator path, Router) are **components inside** this pipeline. The product is the operational outcome: fewer manual email loops, consistent rule application, and auditable decisions.

## Part 1 outcome

Given a trade document (for example invoice or Bill of Lading), Nova should:

1. Extract required fields with confidence and evidence
2. Apply customer-specific rules → MATCH / MISMATCH / UNCERTAIN
3. Route → AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST
4. Persist results and make them queryable (including natural-language query)
5. Expose a minimal operations UI for review

## Part 2 (later)

Email/file triggers, multiple attachments, cross-document validation, draft replies, human approval, and outbound sending — **forward-compatible extension points only** in Part 1.

## Related documents

- [problem-statement.md](./problem-statement.md)
- [personas.md](./personas.md)
- [jtbd.md](./jtbd.md)
- [system-of-outcomes.md](./system-of-outcomes.md)
- [success-metrics.md](./success-metrics.md)
- Requirements: [`../requirements/assignment-overview.md`](../requirements/assignment-overview.md)
