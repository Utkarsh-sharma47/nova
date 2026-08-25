# Frontend deployment

## Local development

```bash
cd frontend
cp .env.example .env
# Align VITE_API_AUTH_TOKEN with API_AUTH_TOKEN
npm install
npm run dev
```

Defaults: Vite on `http://localhost:5173`, API on `http://localhost:8000`.

## Production build

```bash
cd frontend
npm run build
# static assets in frontend/dist
```

Environment variables (build-time for Vite):

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` | API origin; empty string = same-origin (nginx proxy) |
| `VITE_API_AUTH_TOKEN` | Local/demo shared API token (never commit real production secrets) |

## Docker

`frontend/Dockerfile` multi-stage: Node build → nginx Alpine serving `dist/` with SPA fallback.

Compose service `web` (port `8080` by default) proxies `/v1`, `/health`, `/ready` to `api`.

```bash
docker compose up --build
```

Existing `api` and `db` services remain unchanged in role; `web` is additive.

## Related

- [`local.md`](./local.md)
- [`architecture.md`](./architecture.md)
- [`../operations/ui-demo.md`](../operations/ui-demo.md)
