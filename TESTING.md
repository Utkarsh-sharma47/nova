# Testing

Testing strategy for Nova.

## Goals

- Protect extraction, validation, and decision contracts.
- Catch regressions in rule evaluation and agent behavior.
- Protect document intake validation and processor adapters.
- Support honest reporting of quality (see also [docs/evaluation/](docs/evaluation/)).

## Current status

| Suite | Location | Status |
|-------|----------|--------|
| Contract/schema | `tests/contracts/` | Phase 2 |
| Document processing | `tests/documents/` | **Phase 3** |

```bash
pip install -e ".[dev]"
pytest -q
pytest -q tests/documents
python scripts/benchmark_document_processing.py
```

Tooling: **pytest** (+ pytest-asyncio reserved), **Ruff**, **MyPy** ([ADR-0002](docs/decisions/0002-backend-stack.md)).

Document processing coverage: [`docs/testing/document-processing.md`](docs/testing/document-processing.md).  
Required future suites: [`docs/testing/contract-requirements.md`](docs/testing/contract-requirements.md).  
Philosophy: [`docs/testing/philosophy.md`](docs/testing/philosophy.md).

## Test layers

| Layer | Intent | Status |
|-------|--------|--------|
| Unit | Intake validation, adapters, security helpers | **Phase 3 documents** |
| Contract | Stable schemas for agent I/O and processor results | **Phase 2 + Phase 3** |
| Integration | Blob store ↔ processor | **Phase 3 documents** |
| End-to-end | Document in → decision out | Later phases |
| Evaluation | Accuracy on curated sets | Later phases |
| Failure | Timeouts, provider errors | Later phases |

## Expectations for contributors

- New behavior includes tests at the appropriate layer.
- Bug fixes include a regression test when feasible.
- Run relevant tests before claiming success.
- Do not fabricate test results. If tests cannot run, say so.

## Fixtures and data

- Prefer synthetic or anonymized documents (`tests/documents/fixtures.py`).
- Never commit real customer PII or production documents.

## Related documents

- [docs/testing/](docs/testing/)
- [docs/testing/document-processing.md](docs/testing/document-processing.md)
