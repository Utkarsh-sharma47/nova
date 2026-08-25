# Frontend deployment

## Local development (Vite)

```bash
cd frontend
cp .env.example .env
# Align VITE_API_AUTH_TOKEN with API_AUTH_TOKEN on the API
npm install
npm run dev
```

Defaults: Vite on `http://localhost:5173`, API on `http://localhost:8000`.

Build-time Vite variables are acceptable **only** for this local demo path.

## Production / Compose image

Multi-stage `frontend/Dockerfile`:

1. **Build:** Node 22 Alpine runs `npm ci` + `npm run build` with `VITE_API_BASE_URL` (Compose: empty string). **Do not** pass `VITE_API_AUTH_TOKEN` as a build-arg for production images.
2. **Runtime:** `nginxinc/nginx-unprivileged:*-alpine` serves `dist/` on port **8080**, SPA fallback, gzip.

Entrypoint `frontend/docker-entrypoint.sh`:

- Reads `API_AUTH_TOKEN` / `VITE_API_BASE_URL` from the container environment
- Writes `/usr/share/nginx/html/runtime-config.js` defining `window.__NOVA_RUNTIME__`
- Then execs nginx

Nginx proxies `/v1`, `/health`, `/ready`, and `/metrics` to `api:8000`. `client_max_body_size` aligns with API request limits (~12m). `/runtime-config.js` is served with `Cache-Control: no-store`.

```bash
docker compose up --build
# UI: http://localhost:8080
```

## No baked auth

| Path | Auth token source |
|------|-------------------|
| Compose `web` | Runtime `API_AUTH_TOKEN` → `__NOVA_RUNTIME__.apiAuthToken` |
| Local Vite | `VITE_API_AUTH_TOKEN` in `frontend/.env` (gitignored) |
| CI web image build | No token env; image must remain free of secrets |

Never commit real production tokens. Prefer rotating any token that was previously baked into an image layer.

## Related

- [`local.md`](./local.md) · [`architecture.md`](./architecture.md) · [`configuration.md`](./configuration.md)
- [`../architecture/frontend.md`](../architecture/frontend.md)
- [`../operations/ui-demo.md`](../operations/ui-demo.md)
- [`../security/architecture.md`](../security/architecture.md)
