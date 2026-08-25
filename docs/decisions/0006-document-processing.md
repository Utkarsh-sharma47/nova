# ADR-0006: Document processing architecture

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-08-25 |
| Deciders | Principal Software Architect (Phase 2) |
| Supersedes | — |
| Superseded by | — |

## Context

### Problem

Nova must accept trade documents and produce text/layout signals for the Extractor without hard-wiring one OCR vendor.

### Requirements

- Pluggable bytes → `DocumentContent`
- Support clean digital PDFs and messy scans
- Security: type/size limits (implementation deferred, designed now)
- Evidence references must be representable

## Decision

Introduce a **`DocumentProcessorPort`**:

```text
DocumentProcessorPort.process(blob, media_type) -> DocumentContent
```

Part 1 adapters (implement later): DigitalPdfAdapter, OcrAdapter, PassthroughTextAdapter (tests).

Extractor consumes `DocumentContent`, not raw vendor payloads.

## Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| Multimodal LLM-only | Simple pipeline | Costly; weaker evidence; hard offline tests |
| Single cloud OCR hard-coded | High quality | Lock-in; offline CI pain |
| Commercial IDP platform | Strong extraction | Hides agent architecture |

## Consequences

### Advantages

Swap OCR without changing Extractor contracts; fixtures inject `DocumentContent`.

### Disadvantages

Two-stage errors (processor + extractor) need clear taxonomy.

### Operational cost

OCR may add CPU or cloud cost; keep configurable.

### Complexity

Moderate; start with PDF text + one OCR path.

### Developer velocity

Adapters isolate native deps from domain.

### Testing implications

Golden tests can skip OCR by feeding `DocumentContent`.

### Deployment implications

OCR packages may enlarge images.

### Part 2 compatibility

Email attachments map to the same processor port.

### Migration risk

Low if `DocumentContent` remains stable.

## Compliance

- Do not call OCR inside FastAPI routes; use ingestion service.
- Record processor version on document versions.

## References

- `REQ-EXT-001`–`006`, `REQ-SEC-004`
