# Pipeline integration testing

Phase 7 end-to-end tests live in `tests/pipeline/test_pipeline_e2e.py`.

Coverage includes: valid invoice/BoL happy paths, missing/ambiguous fields,
HUMAN_REVIEW / AMENDMENT_REQUEST, extractor/validator/router failures,
malformed LLM output, LLM timeout, database failure helper, duplicate
ingestion, idempotent replay, invalid lifecycle transitions, system_failsafe,
unsafe AUTO_APPROVE rejection, and full run traceability.

All tests use `MockLLM` (no provider credentials).

Run:

```bash
pytest -q tests/pipeline/
```
