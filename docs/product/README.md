# Product

Product definition for Nova: who it serves, what jobs it completes, and how verification fits operations.

## Product summary

Nova is an **operational trade/shipping document verification system**. It extracts fields from documents such as invoices and Bills of Lading, checks customer-specific rules, and routes outcomes to AUTO_APPROVE, HUMAN_REVIEW, or AMENDMENT_REQUEST — reducing manual email loops between shippers and validation teams.

## Documents (Phase 1)

| Document | Status |
|----------|--------|
| [problem-definition.md](./problem-definition.md) | Done |
| [solution-definition.md](./solution-definition.md) | Done — conceptual pipeline |
| [personas-and-users.md](./personas-and-users.md) | Done |

## Guidance

- Keep workflows outcome-oriented.
- Defer technical design to [`../architecture/`](../architecture/) and [`../features/`](../features/).
- Do not specify UI frameworks or vendors here until chosen via ADR.

## Related

- [Requirements](../requirements/)
- [Features](../features/)
- [Part 1 scope](../features/part1-scope.md)
