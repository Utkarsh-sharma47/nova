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

Invoice: `invoice_number`, `invoice_date`, `seller_name`, `buyer_name`, `currency`, `total_amount`

Bill of Lading: `bl_number`, `vessel_name`, `shipper_name`, `consignee_name`,
`port_of_loading`, `port_of_discharge`, `container_number`

## Anti-fabrication

- `KNOWN` requires non-null value + grounded evidence snippet present in document text
- Unsupported / unrequested fields rejected
- Malformed LLM JSON → retry → `FAILED`
- Prompt injection in document text cannot add illegal fields or bypass schema

## Non-goals

Validator, Router, live OpenAI/Anthropic adapters, OCR, frontend.
