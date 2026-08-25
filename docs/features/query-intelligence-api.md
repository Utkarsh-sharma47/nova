# Feature: Query / Intelligence API

## Summary

Phase 8 implements grounded natural-language query over Nova’s system of record via `POST /v1/query`. Operators ask supported business questions; the system classifies to an allow-listed intent and answers only from parameterized PostgreSQL/SQLite reads.

## Requirements

- `REQ-QUERY-001` — query layer over persisted data
- `REQ-QUERY-002` — natural-language query over verification data
- `REQ-QUERY-003` — must not invent facts not present in persisted data
- `REQ-SEC-*` — no arbitrary SQL / prompt abuse leading to data exfiltration

## Behavior

Supported intents (Part 1):

- shipment / document status
- validation status and failing checks
- decision disposition and reasons
- list shipments by decision
- list documents for shipment
- summarize a verification run (extraction + validation + decision)
- count / list documents by agreement category (`STRONG_AGREEMENT` / `PARTIAL_AGREEMENT` / `WEAK_AGREEMENT`)
- count documents requiring attention (partial + weak)
- count documents by decision disposition
- count documents with validation mismatches

Unsupported / unsafe questions return structured `UNSUPPORTED` (never fabricated success).

Agreement classification is derived deterministically from persisted extraction confidence
and validation outcomes. It does **not** replace Router decisions.

## Architecture

```text
API → QueryService → classifier (security + deterministic + optional LLM)
                  → QueryRepository (SQLAlchemy, customer-scoped)
                  → QueryResponse (RESULT | EMPTY | UNSUPPORTED | FAILURE)
```

Persistence tables used for reads: Phase 7 `validations` (checks embedded in
`result_json`) and `decisions` (Alembic `0003_phase6_decisions` + `0004_phase7_pipeline`).
No separate Phase 8 schema migration is required on the Phase 7 lineage.

## LLM boundary

LLM may classify intent only. Final factual values come exclusively from repository results.

## Security

See [../security/query-api.md](../security/query-api.md). Tests cover SQL injection, prompt injection, schema discovery, and invented intents.

## Testing

`tests/query/` — supported intents, security, API validation, LLM/DB failure modes. Fixtures seed deterministic SoR rows and assert returned IDs exist in the seed.

## Part 2

Additional intents and RBAC without opening a free-form SQL channel.

## Related

- [../api/query-interface.md](../api/query-interface.md)
- `src/nova/query/`
- `src/nova/contracts/query.py`
