# Extractor agent (feature)

Phase 4 implements the Extractor Agent against frozen Phase 2 contracts.

## Flow

```text
stored (content_available)
  → processing (in_pipeline)
  → extraction (ExtractorService via LLMPort)
  → processed (extracted) | failed
```

Ingestion still returns `202 ACCEPTED`. The application then runs extraction
(synchronously in Part 1) using `MockLLM` by default. `GET /v1/documents/{id}`
projects `EXTRACTED` or `FAILED` with an extraction summary.

## Components

| Component | Role |
|-----------|------|
| `LLMPort` / `MockLLM` | Provider-agnostic completion; CI uses MockLLM |
| `ExtractorService` | Prompt build, bounded retry (max 2), schema validation, anti-fabrication |
| `ExtractionApplicationService` | Lifecycle + append-only persistence |
| Prompts | Versioned `extractor.v1` (`prompt_id=extractor.part1`) |

## Part 1 fields

**GoComet assignment MUST fields** (always requested for invoice and BoL):

`consignee_name`, `hs_code`, `port_of_loading`, `port_of_discharge`, `incoterms`,
`description_of_goods`, `gross_weight`, `invoice_number`

Invoice also includes: `invoice_date`, `seller_name`, `buyer_name`, `currency`, `total_amount`

Bill of Lading also includes: `bl_number`, `vessel_name`, `shipper_name`, `container_number`

Images (PNG/JPEG) are accepted via `RasterImageAdapter` and passed to vision-capable
`LLMPort` adapters. Without live credentials, MockLLM leaves unread fields `MISSING`.

## Anti-fabrication

- `KNOWN` requires non-null value + grounded evidence snippet present in document text
- Unsupported / unrequested fields rejected
- Malformed LLM JSON → retry → `FAILED`
- Prompt injection in document text cannot add illegal fields or bypass schema

## Non-goals

Validator, Router, live OpenAI/Anthropic adapters, OCR, frontend.
