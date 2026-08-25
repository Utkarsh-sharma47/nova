# Frontend architecture (Part 1)

## Stack

React + TypeScript + Vite ([ADR-0009](../decisions/0009-frontend-stack.md)).

Location: `frontend/`.

## Layering

```text
Pages (routes)
  → components (presentation)
  → hooks (local async state)
  → api/ (typed HTTP client)
  → Nova HTTP API
```

No Redux. Shared fetching uses a small `useAsync` hook. Business rules remain on the backend.

## Routes

See [`../features/operations-ui.md`](../features/operations-ui.md).

## API client

`frontend/src/api/client.ts` centralizes:

- base URL — Compose/runtime prefers `window.__NOVA_RUNTIME__.apiBaseUrl`; otherwise `VITE_API_BASE_URL` (empty = same-origin)
- auth headers — Compose injects `window.__NOVA_RUNTIME__.apiAuthToken` at container start via `/runtime-config.js` (see `frontend/src/runtime-config.ts`); local Vite may use build-time `VITE_API_AUTH_TOKEN` → Bearer + `X-API-Key`
- timeouts
- structured error parsing (`code`, `message`, `details`, `trace_id`, `retryable`)

Production Compose **must not** bake auth tokens into the static build. Runtime config is the source of truth for containerized UI auth.

## Styling

Single global stylesheet with CSS variables (navy/slate ops theme). No large UI kit.
No gradients or decorative motion.

## Backend support added for UI

Justified Part 1 reads:

| Endpoint | Why |
|----------|-----|
| `GET /v1/ops/summary` | Dashboard aggregates without inventing numbers |
| `GET /v1/documents?customer_id=` | Recent document list |
| `POST /v1/customers` | Bootstrap a customer for demos/local ops |

Query API (`POST /v1/query`) is adapted onto the Phase 7 validation/decision schema.

## Part 2

UI can add approval workflows and email adapters without changing the typed client boundary;
new pages consume additional APIs behind the same client module.

## Related

- [`technology-stack.md`](./technology-stack.md)
- [`part2-extension-points.md`](./part2-extension-points.md)
