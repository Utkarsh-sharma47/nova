# Frontend testing

## Tooling

- Vitest
- Testing Library (React + user-event)
- jsdom

Run from `frontend/`:

```bash
npm test
npm run typecheck
npm run build
```

## Coverage expectations

Deterministic mocked fetch tests for:

- upload success / client validation / 422 / 409 idempotency conflict
- document loading and extraction/validation/decision rendering
- HUMAN_REVIEW and AMENDMENT_REQUEST presentation
- query RESULT / EMPTY / UNSUPPORTED / FAILURE
- network failure and loading states
- unsafe HTML from API payloads is not executed (assert text content)

Production services are not required for unit/component tests.

## Demo / smoke

Manual flow: [`../operations/ui-demo.md`](../operations/ui-demo.md).

## Related

- [`../features/operations-ui.md`](../features/operations-ui.md)
- Backend suite remains authoritative for pipeline correctness (`pytest`)
