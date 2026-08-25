# Nova architecture diagram (GoComet submission)

Source-controlled Mermaid diagram for Part 1 with Part 2 extension points marked.

```mermaid
flowchart TB
  subgraph part1 [Part 1 — implemented]
    User([User / CG operator])
    UI[React Frontend]
    API[FastAPI API]
    Ing[Ingestion Service]
    Store[(Document Storage FS)]
    Proc[Document Processor Port]
    Ext[Extractor Agent]
    LLM[LLMPort<br/>MockLLM / OpenAI-compatible]
    Val[Validator Agent]
    Rules[Rule Engine]
    Rtr[Router]
    PG[(PostgreSQL)]
    Query[Query Service]
    Obs[Observability<br/>logs + metrics]
    Eval[Evaluation Suites]

    User -->|upload / inspect / query| UI
    UI -->|HTTP /v1| API
    API --> Ing
    Ing -->|store blob| Store
    Ing -->|process bytes| Proc
    Proc -->|DocumentContent text/images| Ext
    Ext -->|complete + optional vision| LLM
    Ext -->|ExtractionResult| Val
    Val --> Rules
    Val -->|ValidationResult| Rtr
    Rtr -->|DecisionResult| PG
    Ext -->|append-only fields| PG
    Val -->|append-only checks| PG
    Ing -->|document / run lifecycle| PG
    API --> Query
    Query -->|parameterized reads| PG
    Query --> API
    API --> UI
    API -.-> Obs
    Ext -.-> Obs
    Val -.-> Obs
    Rtr -.-> Obs
    Eval -.->|gates FA=0 / fabrication=0| Ext
    Eval -.-> Val
    Eval -.-> Rtr
  end

  subgraph part2 [Part 2 — extension points only]
    Email[Email / file triggers]
    Multi[Multi-doc / cross-doc validation]
    Approve[Human approval actions]
    Outbound[Draft replies / outbound send]
  end

  Email -.->|future IngestionPort adapter| Ing
  Multi -.->|future Validation context| Val
  Approve -.->|future engagement UX| UI
  Outbound -.->|future CommunicationPort| API
```

## Arrow legend

| Style | Meaning |
|-------|---------|
| Solid | Part 1 document flow, agent handoffs, persistence, query |
| Dotted to Obs | Correlation IDs / metrics (non-blocking) |
| Dotted Part 2 | Planned extension points — **not implemented** |

## Notes

- Domain logic does not import vendor SDKs; adapters implement `DocumentProcessorPort` and `LLMPort`.
- Router policy is authoritative for disposition; LLM advice cannot force `AUTO_APPROVE`.
- Full narrative: [technical-writeup.md](./technical-writeup.md), root [ARCHITECTURE.md](../../ARCHITECTURE.md).
