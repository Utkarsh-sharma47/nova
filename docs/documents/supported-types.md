# Supported document types (Part 1)

## Allow-list

| Media type | Extension | Adapter | Notes |
|------------|-----------|---------|-------|
| `application/pdf` | `.pdf` | `digital_pdf` (pypdf) | Digital PDFs with embedded text |
| `text/plain` | `.txt` | `passthrough_text` | Fixtures / deterministic tests |

## Validation rules

1. Detect media type from **magic bytes** (do not trust extension alone).
2. Reject unsupported extensions and MIME types with `DOC_*` errors.
3. Reject declared MIME / extension mismatches.
4. Enforce max size (default **10 MiB**) and max pages (default **100**).
5. Require basic PDF integrity (`%PDF` header + `%%EOF` near end).

## Explicitly deferred

| Type | Reason |
|------|--------|
| Image-only / scanned PDFs needing OCR | OCR adapter reserved; Part 1 starts with digital PDFs |
| `image/png`, `image/jpeg`, `image/tiff` | Require OCR; not enabled in processor allow-list |
| Office formats (DOCX, XLSX) | Out of Part 1 scope |
| Encrypted PDFs | Rejected as `DOC_UNREADABLE` |

Business document classes (`INVOICE`, `BILL_OF_LADING`) are **hints** on the processing request — this layer does not classify trade-document meaning.
