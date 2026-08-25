# Phase 10 system verification

Phase 10 proves Nova Part 1 as one end-to-end application: upload → process →
extract → validate → route → persist → query/UI-facing APIs.

## Suite layout

| Path | Purpose |
|------|---------|
| `tests/e2e/test_phase10_matrix.py` | Canonical **33-case** E2E matrix |
| `tests/e2e/test_data_integrity.py` | Append-only AI history / idempotent replay |
| `tests/e2e/test_api_contracts.py` | Documented endpoint smoke (status + shapes) |
| `tests/pipeline/` | Phase 7 pipeline integration (retained) |
| `tests/query/` | Phase 8 grounded query + security |
| `frontend/` Vitest | Phase 9 UI workflows (mocked fetch) |

## 33-case matrix mapping

| # | Case | Primary test |
|---|------|--------------|
| 1 | Valid invoice | `test_m01_valid_invoice` |
| 2 | Valid Bill of Lading | `test_m02_valid_bol` |
| 3 | Missing required field | `test_m03_missing_required_field` |
| 4 | UNKNOWN field | `test_m04_unknown_field` |
| 5 | AMBIGUOUS field | `test_m05_ambiguous_field` |
| 6 | MISMATCH validation | `test_m06_mismatch_validation` |
| 7 | UNCERTAIN validation | `test_m07_uncertain_validation` |
| 8 | HUMAN_REVIEW | `test_m08_human_review` |
| 9 | AMENDMENT_REQUEST | `test_m09_amendment_request` |
| 10 | AUTO_APPROVE | `test_m10_auto_approve` |
| 11 | Extractor failure | `test_m11_extractor_failure` |
| 12 | Validator failure | `test_m12_validator_failure` |
| 13 | Router failure | `test_m13_router_failure` |
| 14 | Malformed LLM output | `test_m14_malformed_llm_output` |
| 15 | LLM timeout | `test_m15_llm_timeout` |
| 16 | LLM/provider failure | `test_m16_llm_provider_failure` |
| 17 | Corrupted document | `test_m17_corrupted_document` |
| 18 | Unsupported document | `test_m18_unsupported_document` |
| 19 | Oversized document | `test_m19_oversized_document` |
| 20 | Malicious filename / path traversal | `test_m20_malicious_filename_path_traversal` |
| 21 | MIME/extension mismatch | `test_m21_mime_extension_mismatch` |
| 22 | Duplicate upload | `test_m22_duplicate_upload` |
| 23 | Idempotency replay | `test_m23_idempotency_replay` |
| 24 | Idempotency key reuse (different content) | `test_m24_idempotency_key_reuse_different_content` |
| 25 | Database failure | `test_m25_database_failure` |
| 26 | Invalid state transition | `test_m26_invalid_state_transition` |
| 27 | system_failsafe | `test_m27_system_failsafe` |
| 28 | Unsafe AUTO_APPROVE attempt | `test_m28_unsafe_auto_approve_attempt` |
| 29 | Unsupported query | `test_m29_unsupported_query` |
| 30 | SQL injection query | `test_m30_sql_injection_query` |
| 31 | Prompt injection query | `test_m31_prompt_injection_query` |
| 32 | Query missing entity | `test_m32_query_missing_entity` |
| 33 | Successful grounded query | `test_m33_successful_grounded_query` |

All matrix cases use **MockLLM** only.

## Commands

```bash
pytest -q tests/e2e/
pytest -q
python scripts/run_full_evaluation.py
cd frontend && npm test && npm run typecheck && npm run build
```

## Related

- [pipeline-integration.md](./pipeline-integration.md)
- [query-api.md](./query-api.md)
- [frontend.md](./frontend.md)
- [failure-testing.md](./failure-testing.md)
- Audit: [`docs/audits/phase-10-audit.md`](../audits/phase-10-audit.md)
