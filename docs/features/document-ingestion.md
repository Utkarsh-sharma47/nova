# Document ingestion

Phase 3 accepts authenticated PDF and UTF-8 text uploads or pre-staged paths at
`POST /v1/documents`. Source paths must be relative and resolve beneath
`DOCUMENT_STORAGE_PATH`; arbitrary absolute server paths are rejected. The caller supplies a customer, optional shipment,
document type, optional external reference, and required `Idempotency-Key`.
Successful requests return `202 Accepted`.

The application validates size, allow-listed media type, extension/content
agreement, and filename safety. It normalizes digital content through
`DocumentProcessorPort`, writes bytes through `DocumentStoragePort`, and
atomically records the document, immutable first version, queued verification
run, and idempotency response.

After accept, the Extractor Agent runs (`LLMPort`, default `MockLLM`) and
advances lifecycle `content_available → in_pipeline → extracted|failed`.
Extraction fields and model/prompt metadata are append-only.

The Part 1 pipeline then continues synchronously (when auto-pipeline is enabled):
Validator → Router → persist validation/decision → `DECIDED` (or fail-closed
`HUMAN_REVIEW` / `FAILED`). See [`end-to-end-pipeline.md`](./end-to-end-pipeline.md).

Equal principal/key/fingerprint requests replay the original identifiers.
Reusing a key for different input returns
`409 IDEMPOTENCY_KEY_REUSE_MISMATCH`. Concurrent requests are resolved by the
database uniqueness constraint: the loser rolls back, removes its stored blob,
then re-reads and replays the winner. Any database failure after a blob write
also triggers best-effort orphan cleanup.

Malware scanning and OCR for scanned PDFs are intentionally out of Part 1 scope
(MIME/size/path validation only). See [`../audits/known-limitations.md`](../audits/known-limitations.md).
