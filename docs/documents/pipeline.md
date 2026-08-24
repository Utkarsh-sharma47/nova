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
 Extractor Agent (future — not implemented in this package)
```

## Statuses

| Status | Meaning |
|--------|---------|
| `SUCCEEDED` | Normalized content available |
| `PARTIAL` | Processed but no/low extractable text (e.g. scan without OCR) |
| `FAILED` | Rejected or unreadable; `error_code` set |

## Non-goals

- No LLM calls
- No business field extraction
- No validation/routing decisions
