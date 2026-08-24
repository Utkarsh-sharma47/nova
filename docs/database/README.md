# Database

Data model and persistence documentation for Nova.

## Purpose

Document entities, schemas, migrations, retention, and access patterns once persistence is chosen.

## Current status

No database technology or schema has been decided. Record the choice as an ADR before documenting vendor-specific details.

## Planned contents

| Topic | Status |
|-------|--------|
| Logical data model | Planned |
| Persistence technology ADR | Planned |
| Migrations policy | Planned |
| Retention and deletion | Planned |

## Guidance

- Prefer documenting the logical model before physical schema.
- Call out PII and document-blob storage requirements; see [`../security/`](../security/).

## Related

- [Architecture](../architecture/)
- [Security](../security/)
- [Decisions](../decisions/)
