# Supported document types (Part 1)

## Allow-list

| Media type | Extension | Adapter | Notes |
|------------|-----------|---------|-------|
| `application/pdf` | `.pdf` | `digital_pdf` (pypdf) | Digital PDFs with embedded text |
| `text/plain` | `.txt` | `passthrough_text` | Fixtures / deterministic tests |
| `image/png` | `.png` | `raster_image` | Bytes preserved for vision LLM; no local OCR |
| `image/jpeg` | `.jpg`, `.jpeg` | `raster_image` | Same as PNG |

## Validation rules

1. Detect media type from **magic bytes** (do not trust extension alone).
2. Reject unsupported extensions and MIME types with `DOC_*` errors.
3. Reject declared MIME / extension mismatches.
4. Enforce max size (default **10 MiB**) and max pages (default **100**).
5. Require basic PDF integrity (`%PDF` header + `%%EOF` near end).
6. PNG/JPEG require valid magic bytes; content is base64-attached for vision providers.

## Vision / LLM configuration

| Setting | Behavior |
|---------|----------|
| `LLM_PROVIDER=mock` (default) | Deterministic MockLLM; image-only docs yield MISSING fields (no fabrication) |
| `LLM_PROVIDER=openai` + `LLM_API_KEY` | OpenAI-compatible chat/vision adapter |
| Missing API key | Falls back to MockLLM with warning |

## Explicitly deferred

| Type | Reason |
|------|--------|
| Image-only / scanned PDFs needing dedicated OCR | Use PNG/JPEG + vision LLM, or future OCR adapter |
| `image/tiff`, `image/gif` | Not in allow-list |
| Office formats (DOCX, XLSX) | Out of Part 1 scope |
| Encrypted PDFs | Rejected as `DOC_UNREADABLE` |

Business document classes (`INVOICE`, `BILL_OF_LADING`) are **hints** on the processing request — this layer does not classify trade-document meaning.
