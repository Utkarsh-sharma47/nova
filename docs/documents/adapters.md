# Adapter architecture

## Port

`DocumentProcessorPort` (ADR-0006):

```text
process(blob, media_type=...) -> DocumentContent
```

Application code depends on the port / `DocumentProcessingService`, not on pypdf.

## Concrete adapters (Part 1)

### `digital_pdf` (pypdf)

| Field | Value |
|-------|-------|
| Technology | [pypdf](https://pypi.org/project/pypdf/) |
| License | BSD-3-Clause |
| Limitations | Embedded text only; no OCR; encrypted PDFs unsupported |
| Accuracy | Good for digitally generated trade PDFs; empty text → `PARTIAL` + warning |
| Deployment | Pure Python; no system packages |

### `passthrough_text`

UTF-8 `text/plain` for fixtures and contract tests.

## OCR

Not implemented. Scanned pages surface `no_extractable_text_ocr_not_configured`. A future `OcrAdapter` can register beside `digital_pdf` without changing Extractor contracts.
