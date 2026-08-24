# Testing: document processing

## Suites

| Path | Coverage |
|------|----------|
| `tests/documents/test_validation.py` | Size, MIME, extension, corrupt PDF, filename security |
| `tests/documents/test_adapters.py` | Port conformance, PDF/text adapters, service |
| `tests/documents/test_contracts.py` | Result schema, error mapping, no fabricated fields |
| `tests/documents/test_storage_integration.py` | LocalBlobStore ↔ processor |
| `tests/documents/test_large_file.py` | Oversized rejection, size vs latency smoke |
| `tests/documents/test_observability.py` | Logs omit document bodies |

## Fixtures

`tests/documents/fixtures.py` builds **synthetic** text invoices and minimal PDFs. Do not commit real customer documents.

## Commands

```bash
pip install -e ".[dev]"
pytest -q tests/documents
ruff check src/nova/documents tests/documents
mypy
```
