# System architecture

Phase 2 freezes the logical architecture. Runtime agents and persistence are implemented in later phases.

## End-to-end flow

```text
Document → Ingestion → Extraction → ExtractionResult
        → Validation → ValidationResult → Routing → DecisionResult
        → Persistence → Query/API → UI
```

## Layer responsibilities

| Layer | Responsibility | Must not |
|-------|----------------|----------|
| **Presentation (UI)** | Ops UX: submit, inspect evidence, view decisions | Embed LLM calls |
| **API** | Authn, request validation, HTTP mapping, idempotency | Call LLM SDKs or OCR vendors directly |
| **Application / orchestration** | Run stages, propagate IDs, timeouts/retries | Own vendor-specific protocols |
| **Domain / AI agents** | Extractor, Validator, Router policies & contracts | Persist directly or know HTTP |
| **Infrastructure** | LLM adapters, document processors, DB, storage | Contain routing business policy |
| **Persistence** | System of record + audit | Interpret LLM free text |

## Ports

| Port | Purpose | Part 2 |
|------|---------|--------|
| `IngestionPort` | Source → document version | Email/file adapters |
| `DocumentProcessorPort` | Bytes → `DocumentContent` | More MIME types |
| `LLMPort` | Structured completion | Draft replies |
| `ValidationPort` | Rules + extractions → result | Multi-doc context |
| `RoutingPort` | Validation → decision | Approval gates |
| `CommunicationPort` | Reserved | Draft/send |

## Trust boundaries

1. HTTP edge — authenticate, authorize, validate size/type.
2. Contract edge — agent I/O parsed with Pydantic.
3. Decision edge — router policy explicit; LLM cannot alone force `AUTO_APPROVE`.

Detail: [layering.md](./layering.md), [ai-architecture.md](./ai-architecture.md), [part2-extension-points.md](./part2-extension-points.md).
