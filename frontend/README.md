# Nova frontend (ops UI)

Minimal React + TypeScript + Vite operations UI for Nova trade document verification.

## Prerequisites

- Node.js 20+ (22 recommended for Docker parity)
- npm 10+

## Environment

Copy the example file and adjust values:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Nova API base URL (no trailing slash) | `http://localhost:8000` |
| `VITE_API_AUTH_TOKEN` | Demo API key sent as `Authorization: Bearer` and `X-API-Key` | unset |

Vite embeds these at **build time**. Restart `npm run dev` after changing `.env`.

Never commit real tokens. Use `.env.example` placeholders only.

## Local development

```bash
npm install
npm run dev
```

Open http://localhost:5173 (Vite default). Ensure the Nova API is running at `VITE_API_BASE_URL`.

## Scripts

| Script | Purpose |
|--------|---------|
| `npm run dev` | Vite dev server with HMR |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Serve production build locally |
| `npm run test` | Vitest unit/integration tests (jsdom) |
| `npm run typecheck` | TypeScript check (`tsc --noEmit`) |
| `npm run lint` | Same as typecheck (no ESLint in this minimal setup) |

## Tests

```bash
npm test
```

Tests mock `fetch` deterministically and live under `src/**/*.test.tsx`.

## Production build

```bash
npm run build
npm run preview
```

## Docker

Build with API URL baked in:

```bash
docker build \
  --build-arg VITE_API_BASE_URL=http://localhost:8000 \
  --build-arg VITE_API_AUTH_TOKEN=your-demo-token \
  -t nova-frontend .
docker run --rm -p 8080:80 nova-frontend
```

The image serves static assets via nginx with SPA fallback. By default the UI calls the absolute `VITE_API_BASE_URL` from the browser. To proxy `/v1` and `/health` through nginx instead, see commented blocks in `nginx.conf`.

## Routes

| Path | Purpose |
|------|---------|
| `/` | Dashboard — ops summary totals, recent documents/decisions |
| `/upload` | Document ingestion (multipart + Idempotency-Key) |
| `/documents/:documentId` | Document detail, extraction, validation, decision |
| `/shipments/:shipmentId` | Shipment identity and linked documents |
| `/query` | Grounded NL query (`POST /v1/query`) |

## API client

All HTTP calls are centralized in `src/api/`. Errors parse the Nova envelope `{ error: { code, message, details, trace_id, retryable } }`.

Some endpoints (`GET /v1/documents`, `GET /v1/ops/summary`, validation/decision/query) are wired per contract and may return 404 until implemented server-side; the UI handles loading, empty, and error states without fabricating data.
