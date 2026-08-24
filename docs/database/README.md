# Database

Data model and persistence notes for Nova.

## Current status

No database schema exists in Phase 1.

## Design constraint already in force

Shipment **1→N** documents must be representable for Part 2 readiness (`REQ-DATA-002`, [Part 2 extension points](../architecture/part2-extension-points.md)), even if Part 1 only persists one document per shipment.

## Planned contents

| Document | Status |
|----------|--------|
| ERD / entity definitions | Phase 2–5 |
| Migration notes | Phase 5 |
| Retention / PII handling notes | Phase 5 (policy started in security baseline) |

## Related

- [Architecture](../architecture/)
- [Security baseline](../security/baseline.md)
- Requirements `REQ-DATA-*`
