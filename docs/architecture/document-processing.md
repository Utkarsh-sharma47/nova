# Architecture: document processing

Phase 3 implements ADR-0006 behind `nova.documents`.

## Boundary

```text
uploaded document bytes
        ↓
DocumentProcessingService (+ validation)
        ↓
DocumentProcessorPort adapters
        ↓
DocumentContent / DocumentProcessingResult → atomic DocumentStoragePort write
        ↓
Extractor (Phase 3+/4 — not in this change)
```

## Package map

| Module | Role |
|--------|------|
| `nova.documents.port` | `DocumentProcessorPort` |
| `nova.documents.models` | Request/result models |
| `nova.documents.validation` | Intake validation |
| `nova.documents.security` | Filename / path safety |
| `nova.documents.adapters.*` | pypdf + passthrough |
| `nova.documents.storage.*` | Generic blob-store port and standalone local adapter |
| `nova.documents.service` | Orchestration + observability |

The application ingestion service uses this single processor stack. Its
`LocalFilesystemStorage` adapter remains the persistence boundary because it
writes via a temporary file, fsyncs, and atomically renames. If the database
transaction fails after that write, ingestion deletes the orphan. The
standalone `LocalBlobStore` remains covered for package-level tests.

## Failure modes

| Code | Typical cause | Retryable |
|------|---------------|-----------|
| `DOC_UNSUPPORTED_*` | Allow-list miss | no |
| `DOC_MIME_MISMATCH` | Spoofed type | no |
| `DOC_PAYLOAD_TOO_LARGE` | Over size limit | no |
| `DOC_CORRUPT` / `DOC_UNREADABLE` | Bad/encrypted PDF | no |
| `DOC_PATH_TRAVERSAL` | Unsafe path/name | no |
| `DOC_INTERNAL` | Unexpected adapter failure | sometimes |

## Part 2

Email/file adapters feed the same processor port; MIME allow-list can expand without changing `DocumentContent`.
