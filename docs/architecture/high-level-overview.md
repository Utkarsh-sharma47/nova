# High-level architecture overview

Phase 1 status: **conceptual only**. No runtime services are implemented yet.

```text
                    ┌─────────────────────────────────────────┐
                    │           Operations UI (Part 1)         │
                    └───────────────────┬─────────────────────┘
                                        │
                    ┌───────────────────▼─────────────────────┐
                    │         API / Application layer          │
                    └───────────────────┬─────────────────────┘
                                        │
        ┌───────────────┬───────────────┼───────────────┬──────────────┐
        ▼               ▼               ▼               ▼              ▼
   Ingestion port   Extractor       Validator        Router        Query
   (UI/path now;    Agent           (rules ± LLM)    Agent         (API + NL)
    email later)
        │               │               │               │              │
        └───────────────┴───────┬───────┴───────────────┘              │
                                ▼                                      │
                         Persistence store ◄────────────────────────────┘
                     (shipment, docs, validations, decisions)
```

## Logical components (future)

| Component | Responsibility |
|-----------|----------------|
| Ingestion port | Normalize incoming documents into a run |
| Extractor Agent | Fields + confidence + evidence |
| Validator | Customer rules → MATCH/MISMATCH/UNCERTAIN |
| Router Agent | AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST |
| Persistence | System of record |
| Query | Retrieval + grounded NL answers |
| UI | Minimal B2B ops surface |
| Observability | Logs, traces, cost metrics |

Technology choices (language, framework, DB, LLM provider) will be recorded in ADRs during Phase 2 before coding.
