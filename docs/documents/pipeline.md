# Document processing pipeline

```text
blob (+ optional filename / declared MIME)
        │
        ▼
 intake validation (size, extension, magic MIME, integrity, filename sanitization)
        │
        ▼
 adapter selection (DocumentProcessorPort registry)
        │
        ▼
 adapter.process(blob) → DocumentContent
        │
        ▼
 DocumentProcessingResult (status, source metadata, warnings, duration)
        │
        ▼
 Extractor Agent (Phase 4 — `ExtractorService` via `LLMPort`)
```

## Statuses

| Status | Meaning |
|--------|---------|
| `SUCCEEDED` | Normalized content available |
| `PARTIAL` | Processed but no/low extractable text (e.g. scan without OCR) |
| `FAILED` | Rejected or unreadable; `error_code` set |

## Non-goals (document package)

- No business field extraction inside adapters (Extractor owns that)
- No validation/routing decisions
- No live LLM vendor SDK in this package
