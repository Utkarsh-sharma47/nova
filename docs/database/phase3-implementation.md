# Phase 3 database implementation

Migration: `alembic/versions/0001_phase3_foundation.py`

## Tables

| Table | Purpose |
|-------|---------|
| `customers` | Tenant / customer root |
| `shipments` | Shipment under a customer |
| `documents` | Document metadata (`received`…`withdrawn`) |
| `document_versions` | Immutable content versions + SHA-256 |
| `verification_runs` | Queued (not executed) pipeline runs |
| `idempotency_records` | HTTP `Idempotency-Key` replay store |

ORM models: `src/nova/persistence/models.py`  
Never use `Base.metadata.create_all` in production; tests and runtime apply Alembic.

## Deferred

- Full AI/validation/decision tables
- `decisions` failsafe CHECK (`system_failsafe` cannot `AUTO_APPROVE`) — deferred until decisions table lands

## Document statuses (CHECK)

`received | stored | processing | processed | failed | superseded | withdrawn`
