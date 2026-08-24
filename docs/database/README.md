# Database

Data model and persistence documentation for Nova.

## Purpose

Define the logical domain model, PostgreSQL physical schema, relationships, indexing, audit strategy, and database test requirements for the system of record.

## Current status

| Topic | Status |
|-------|--------|
| Persistence technology | **Accepted:** PostgreSQL ([ADR-0002](../decisions/0002-postgresql-persistence.md)) |
| Logical domain model | Documented |
| Physical schema design | Documented (migrations not implemented) |
| Indexing strategy | Documented |
| Audit model | Documented |
| Database test plan | Documented (tests not implemented) |
| Repositories / ORM | Not started (Phase 5) |

## Design constraints in force

- Shipment **1→N** documents (`REQ-DATA-002`); never model a permanent single-file shipment.
- Structured AI outputs (values, confidence, evidence, validation results, decision factors, model/prompt metadata) remain **queryable**.
- Decisions and audit events are **append-only**; Part 2 approvals add records without rewriting router dispositions.
- Object storage holds document bytes; PostgreSQL stores URIs + hashes + pipeline data.

## Contents

| Document | Description |
|----------|-------------|
| [domain-model.md](./domain-model.md) | Entities, lifecycles, invariants, data classification |
| [schema-design.md](./schema-design.md) | Tables, keys, constraints, soft-delete, AI storage, Part 2 stubs |
| [relationships.md](./relationships.md) | Cardinality, FKs, ER diagram |
| [indexing-strategy.md](./indexing-strategy.md) | Unique, FK, queue, and audit indexes |
| [audit-model.md](./audit-model.md) | Audit stream vs domain history |
| [database-test-plan.md](./database-test-plan.md) | FK/uniqueness/idempotency/transaction tests |

## Related

- [Architecture](../architecture/)
- [Decisions](../decisions/)
- [Security](../security/)
- [Testing](../testing/)
- Requirements `REQ-DATA-*`, `REQ-PART2-*`
