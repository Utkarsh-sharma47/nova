# Query / Intelligence API testing

Phase 8 automated coverage for `POST /v1/query` and the controlled query layer.

## Suites

| Path | Focus |
|------|-------|
| `tests/query/test_query_supported.py` | Allow-listed intents, empty/missing, grounding |
| `tests/query/test_query_security.py` | SQL injection, prompt injection, schema discovery, arbitrary SQL |
| `tests/query/test_query_failures.py` | API validation, LLM timeout/malformed/invented intent, DB failure |
| `tests/contracts/test_query_schemas.py` | Pydantic request/response contracts |

## Fixtures

`tests/query/conftest.py` seeds customers, shipments, documents, runs, extracted fields, validations/checks, and decisions. Assertions require returned factual IDs to match the seed.

## How to run

```bash
pytest tests/query tests/contracts/test_query_schemas.py -q
```

Uses MockLLM only; no live provider credentials.

## Related

- [../api/query-interface.md](../api/query-interface.md)
- [../features/query-intelligence-api.md](../features/query-intelligence-api.md)
- [../security/query-api.md](../security/query-api.md)
