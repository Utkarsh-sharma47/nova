# Agent: Extractor

| Field | Value |
|-------|-------|
| Status | Proposed (contract defined; not implemented) |
| Owner | AI Systems Architect |
| Last updated | 2026-08-25 |
| Related ADR(s) | [ADR-0010](../decisions/0010-ai-agent-contracts-and-trust-model.md) |
| Related feature(s) | Part 1 document verification pipeline |
| Contract | [contracts.md](./contracts.md#extractor-contract) |

## 1. Purpose

Read an ingested trade/shipping document and produce a typed field map with **confidence**, **evidence**, and explicit **presence** (`KNOWN` / `UNKNOWN` / `MISSING` / `AMBIGUOUS`).

The Extractor turns unstructured document content into structured inputs for validation. It does not decide business outcomes.

### Responsibilities

- Extract required business fields for the document type (or detect type when asked).
- Attach confidence and evidence for every field attempt.
- Mark absence and ambiguity explicitly; never invent missing values as `KNOWN`.
- Emit structured `ExtractionResult` that passes schema validation.
- Respect timeouts, bounded retries, and cost metadata recording.
- Surface warnings (low OCR quality, partial pages, schema repair).

### Non-responsibilities

- Customer rule evaluation (Validator).
- Routing / approve-review-amend decisions (Router).
- Persistence, UI, or NL query answering.
- Calling outbound communications or drafting shipper emails (Part 2).
- Implementing provider-specific prompt code in this documentation phase.
- Silently “filling in” fields from world knowledge when the document lacks them.

## 2. Inputs

See `ExtractionRequest` in [contracts.md](./contracts.md#extractionrequest).

**Preconditions**

- Document is ingested and addressable via `document_ref`.
- `required_fields` is non-empty for the supported document type.
- `timeout_ms` is set by the orchestrator.

## 3. Outputs

See `ExtractionResult`, `ExtractedField`, `Evidence` in [contracts.md](./contracts.md#extractor-contract).

| Outcome | When |
|---------|------|
| `SUCCEEDED` | All required fields present in the result array with valid presence semantics |
| `PARTIAL` | Some fields extracted; others `UNKNOWN`/`MISSING`/`AMBIGUOUS`, or schema repair applied |
| `FAILED` | Unrecoverable error (timeout exhausted, unreadable document, repeated malformed model output) |

Partial success still produces a typed result for downstream fail-safe routing — not a free-form dump.

## 4. Behavior

1. Load document content via the ingestion handle.
2. Optionally detect `document_type` if not provided.
3. Produce structured fields for `required_fields`.
4. For each field set `presence`, `value`, `confidence`, `uncertainty`, `evidence`, `warnings`.
5. Validate against the Extractor schema before return.
6. On malformed model output: bounded retry → else `FAILED` / `PARTIAL` with errors.

**Anti-fabrication rule:** If the model cannot ground a value, emit `UNKNOWN`, `MISSING`, or `AMBIGUOUS` with `value = null`. Do not coerce guesses into `KNOWN`.

## 5. Dependencies

| Direction | Component |
|-----------|-----------|
| Upstream | Ingestion port / document store |
| Downstream | Validator (consumes `ExtractionResult`) |
| External | LLM provider (future); OCR/layout tools (future, optional) |

## 6. Failure modes

| Failure | Detection | Handling |
|---------|-----------|----------|
| Timeout | Exceeds `timeout_ms` | Stop; `FAILED` or `PARTIAL` with retryable=false if budget exhausted |
| Provider / network error | Transport errors | Bounded retry with backoff; then fail safe |
| Malformed structured output | Schema validation fails | Bounded retry; then `FAILED`/`PARTIAL` + `SCHEMA_REPAIR` uncertainty if partial coerce succeeded |
| Unreadable / empty document | Content checks | `FAILED`; all required fields may be omitted only if status=`FAILED` |
| Unsupported document type | Type detection | `PARTIAL`/`FAILED` with clear error code; do not invent fields |
| Ambiguous field values | Multiple candidates | `AMBIGUOUS`, `value=null`, populate `candidates` |
| Cost / token budget exceeded | Metering | Abort further calls; fail safe |

**Default timeout:** `timeout_ms` supplied per request; recommended orchestrator default **60_000 ms** for Part 1 single-document extraction (configurable later).

**Retry policy:** Max **2** retries (3 total attempts) for retryable errors only (transient provider, malformed JSON). No retry on definitive document emptiness, auth failures, or non-retryable validation errors. No infinite loops.

## 7. Security and data handling

- Treat document bytes and extracted fields as sensitive.
- Do not log full document bodies or secrets; redact snippets in logs per `docs/security/`.
- Do not embed API keys in prompts, fixtures, or evidence.
- Evidence snippets should be minimal and necessary for audit.

## 8. Testing

Contract and schema tests per [agent-evaluation.md](../evaluation/agent-evaluation.md):

- Presence/`value` nullability invariants
- Required fields coverage
- Reject fabricated `KNOWN` with null value
- Malformed output → error path

## 9. Evaluation

- Field-level precision/recall vs gold labels
- Calibration of confidence vs correctness
- Rate of unjustified `KNOWN` (fabrication rate) — must be near zero
- Clean vs messy sample behavior

Harness not built in this phase; metrics defined in evaluation docs.

## 10. Observability

Must emit (when implemented):

- `run_id`, stage=`extractor`, status, latency
- `ModelInvocationMetadata` (model, prompt_version, tokens, cost, attempt)
- Counts of fields by `presence`
- Error codes and retry counts
- No secret material in log fields

## 11. Known limitations

- No runtime implementation yet.
- Document-type field catalogs and OCR strategy are undecided (future ADRs).
- Multi-document extraction is Part 2; contract allows later extension via additional `document_id`s without changing presence semantics.

## 12. Change history

| Date | Change | Author |
|------|--------|--------|
| 2026-08-25 | Initial contract and agent governance doc | AI Systems Architect |
