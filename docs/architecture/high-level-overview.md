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
