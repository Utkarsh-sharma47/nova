# High-level architecture overview

Phase 2 status: **stack and contracts frozen**; runtime services not implemented.

```text
                    ┌─────────────────────────────────────────┐
                    │     Operations UI (React/TS/Vite)       │
                    └───────────────────┬─────────────────────┘
                                        │
                    ┌───────────────────▼─────────────────────┐
                    │         API / FastAPI application        │
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
                      PostgreSQL persistence ◄─────────────────────────┘
                   (shipment, docs, validations, decisions, audit)
```

Stack: [technology-stack.md](./technology-stack.md) · System: [system-architecture.md](./system-architecture.md)

## Query column (Phase 8)

The Query path is read-only over PostgreSQL via allow-listed intents (`POST /v1/query`).
LLM assistance is limited to intent classification; see [../api/query-interface.md](../api/query-interface.md)
and [../features/query-intelligence-api.md](../features/query-intelligence-api.md).
Frontend remains deferred.
