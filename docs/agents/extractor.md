# Agent: Extractor

| Field | Value |
|-------|-------|
| Status | Implemented (MockLLM default; real providers via LLMPort) |
| Owner | AI Systems / Evaluation |
| Last updated | 2026-08-25 |
| Related ADR(s) | [ADR-0010](../decisions/0010-ai-agent-contracts-and-trust-model.md), [ADR-0005](../decisions/0005-ai-provider-abstraction.md) |
| Related feature(s) | Part 1 document verification pipeline |
| Contract | [contracts.md](./contracts.md#extractor-contract), `src/nova/contracts/extraction.py` |
| Runtime | `src/nova/extraction/` |
| Evaluation | `fixtures/evaluation/extractor/`, `scripts/run-extractor-eval.py` |

## 1. Purpose

Read ingested trade/shipping document content and produce a typed field map with **confidence**, **evidence**, and explicit **presence** (`KNOWN` / `UNKNOWN` / `MISSING` / `AMBIGUOUS`).

The Extractor turns unstructured document content into structured inputs for validation. It does not decide business outcomes.

### Responsibilities

- Extract Part 1 catalog fields (`src/nova/extraction/fields.py`).
- Attach confidence and evidence for every field attempt.
- Mark absence and ambiguity explicitly; never invent missing values as `KNOWN`.
- Emit structured `ExtractionResult` that passes schema validation.
- Respect timeouts (default 60s), bounded retries (max 2), and usage metadata.
- Surface warnings (partial pages, schema rejection, unsupported fields).

### Non-responsibilities

- Customer rule evaluation (Validator).
- Routing / approve-review-amend decisions (Router).
- Persistence/UI/NL query.
- Silently filling fields from world knowledge.

## 2. Inputs

`ExtractionRequest` (`src/nova/contracts/extraction.py`):

- Identifiers: `run_id`, `trace_id`, `document_id`, `document_version_id`, `shipment_id`
- `content: DocumentContent` (preferred for this phase) or `document_ref`
- `required_fields` (non-empty; must be in Part 1 catalog)
- `timeout_ms` (default 60_000)
- optional `document_type`, `customer_hints`, `locale`

## 3. Outputs

`ExtractionResult`:

| Status | When |
|--------|------|
| `SUCCEEDED` | Required fields returned with valid presence semantics and no blocking uncertainty |
| `PARTIAL` | Some fields `UNKNOWN`/`MISSING`/`AMBIGUOUS`, or residual uncertainty |
| `FAILED` | Unreadable/empty document, unsupported fields, timeout/retry exhaustion, persistent malformed output |

Each `ExtractedField` includes `presence`, `value`, `confidence`, `uncertainty`, `evidence`, optional `candidates`.

## 4. Prompt lifecycle

| Artifact | Location / value |
|----------|------------------|
| Prompt id | `extractor.part1` |
| Prompt version | `extractor.v1` (`src/nova/extraction/prompts.py`) |
| Agent version | package `nova.__version__` |
| Construction | `build_extraction_prompt(...)` — system rules + required fields + document text |
| Recording | `ModelMetadata.prompt_id` / `prompt_version` / `agent_version` on every result |

**Governance:** prompt/model/agent behavior changes require regression evaluation
(`scripts/run-extractor-eval.py`). See [regression-policy](../evaluation/regression-policy.md)
and [extractor-evaluation](../evaluation/extractor-evaluation.md).

## 5. Behavior

1. Validate `required_fields` against the Part 1 catalog.
2. Reject empty/unreadable content as `FAILED` (`DOCUMENT_UNREADABLE`).
3. Build versioned prompt; call `LLMPort.complete` (default tests use `MockLLM`).
4. Parse JSON → normalize fields with anti-fabrication grounding checks.
5. Fill missing required fields as `UNKNOWN`.
6. On malformed/provider/timeout errors: bounded retry then `FAILED`.

**Anti-fabrication:** `KNOWN` values whose evidence snippet is not present in the
document text are downgraded to `UNKNOWN` with `PARTIAL_EVIDENCE`.

## 6. Failure handling

| Failure | Handling |
|---------|----------|
| Empty / no text | `FAILED` / `DOCUMENT_UNREADABLE` (no LLM call) |
| Unsupported field name | `FAILED` / `UNSUPPORTED_FIELD` |
| Malformed JSON | Retry up to 2×; then `FAILED` / `RETRY_EXHAUSTED` or `MALFORMED_OUTPUT` |
| Provider / timeout | Retry when retryable; then fail safe |
| Fabricated KNOWN | Downgrade field; continue |

## 7. Confidence vs evaluation metrics

- **Production confidence:** per-field `confidence` / `confidence_band` on `ExtractedField` — runtime signal for downstream Validator/Router.
- **Evaluation metrics:** suite rates (accuracy, fabrication rate, …) computed against gold labels — **not** interchangeable with production confidence.

Do not invent statistically meaningful thresholds without measured baselines.

## 8. Evidence

`KNOWN` requires ≥1 evidence entry with `source_type ≠ NONE` and a snippet grounded in document text. Logs must not contain full document bodies or secrets.

## 9. Security

- Document text and extracted fields are sensitive.
- Prompt injection text inside documents must not override extraction rules; post-validate always.
- No API keys in prompts, fixtures, or logs.
- Fixtures are **synthetic only** — never commit real shipping documents.

## 10. Evaluation & dogfooding

```bash
python scripts/run-extractor-eval.py
python scripts/dogfood-extractor.py
pytest -q tests/evaluation tests/extraction
```

Fixed regression dataset: `fixtures/evaluation/extractor` revision `extractor-regression-v1`.

Details: [extractor-evaluation.md](../evaluation/extractor-evaluation.md).

## 11. Observability

Structured logs via `nova.extraction.observability`: start / complete / failure with
`run_id`, `trace_id`, `agent_execution_id`, provider/model, prompt version, latency.
Never log document body, full prompts, or secrets.

## 12. Known limitations

- Default runtime uses `MockLLM` / scripted fixtures — **no real-provider performance claimed**.
- OCR/layout-aware extraction not implemented; text comes from DocumentProcessor.
- Persistence of extraction runs into full domain tables is not completed in this change.
- Validator/Router not implemented here.

## 13. Reproducibility

Record in every eval report: dataset id/revision, `prompt_version`, `agent_version`,
provider/model, git SHA (when available), and per-case pass/fail. Regressions must
be visible (non-zero exit) — never silently accepted.

## 14. Change history

| Date | Change | Author |
|------|--------|--------|
| 2026-08-25 | Initial contract doc | AI Systems Architect |
| 2026-08-25 | Runtime Extractor + deterministic evaluation suite | Evaluation Engineer |
