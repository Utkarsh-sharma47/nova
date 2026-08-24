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

Equal principal/key/fingerprint requests replay the original identifiers.
Reusing a key for different input returns
`409 IDEMPOTENCY_KEY_REUSE_MISMATCH`. Concurrent requests are resolved by the
database uniqueness constraint: the loser rolls back, removes its stored blob,
then re-reads and replays the winner. Any database failure after a blob write
also triggers best-effort orphan cleanup.

Phase 3 stops at `ACCEPTED`: no extraction, validation, routing, malware
scanner, OCR for scanned PDFs, or LLM invocation is implemented.
