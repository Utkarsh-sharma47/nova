# Nova architecture diagram (GoComet submission)

Authoritative Part 1 diagram (Mermaid). Part 2 nodes are extension points only.

```mermaid
flowchart TB
  User([User / CG operator])
  UI[React Frontend]
  API[FastAPI /v1]
  Ing[Ingestion]
  Store[(Document Storage)]
  Proc[DocumentProcessorPort]
  Ext[Extractor]
  LLM{{LLMPort}}
  Mock[MockLLM]
  Vision[OpenAI-compatible vision/text]
  Val[Validator]
  Rules[Rule Engine]
  Rtr[Router]
  PG[(PostgreSQL)]
  Query[Query Service]
  Obs[Observability logs/metrics]

  User --> UI --> API
  API --> Ing
  Ing -->|blob| Store
  Ing -->|bytes| Proc
  Proc -->|DocumentContent| Ext
  Ext --> LLM
  LLM --> Mock
  LLM --> Vision
  Ext -->|ExtractionResult contract| Val
  Val --> Rules
  Val -->|ValidationResult contract| Rtr
  Rtr -->|DecisionResult contract| PG
  Ext -->|append-only fields| PG
  Val -->|append-only checks| PG
  Ing -->|lifecycle + idempotency| PG
  API --> Query --> PG
  Query --> API --> UI
  API -.-> Obs
  Ext -.-> Obs
  Val -.-> Obs
  Rtr -.-> Obs
```

## Boundaries (not drawn as spaghetti)

| Boundary | Behavior |
|----------|----------|
| Processor | PDF / text / PNG / JPEG only; MIME sniff |
| LLM | Domain never imports vendor SDK; adapters only |
| Retry | Extractor bounded retries + timeout; fail closed |
| Router | Hard block on unsafe `AUTO_APPROVE` |
| Query | Allow-listed intents; reject SQL/prompt injection |

## Part 2 extension points (not implemented)

Email/file triggers → Ingestion · Multi-doc validation → Validator · Approval actions → UI · Outbound send → CommunicationPort

Full narrative: [technical-writeup.md](./technical-writeup.md) · Root overview: [ARCHITECTURE.md](../../ARCHITECTURE.md)
