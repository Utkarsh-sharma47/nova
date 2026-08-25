# Feature: End-to-end Part 1 pipeline

**Status:** Implemented (Phase 7)

## Summary

Integrates Extractor, Validator, and Router into one coherent workflow after
document ingestion. Callers receive accurate processing status and can read
validation and decision resources when available.

## User-visible behavior

1. `POST /v1/documents` accepts a document and runs the pipeline synchronously (Part 1)
2. `GET /v1/documents/{id}` reports `DECIDED` / `FAILED` (and intermediate statuses)
3. `GET /v1/documents/{id}/validation` and `/decision` return persisted results
4. Shipment aliases: `/v1/shipments/{id}/validation` and `/decision`

## Non-goals

- Part 2 email ingestion, multi-doc validation, human approval UI
- Live vendor LLM adapters (MockLLM remains default)

## Safety

- Never invent validation/decision on extractor failure
- Never AUTO_APPROVE under uncertainty / failsafe / unsafe LLM suggestion
