# Configuration reference

All secrets and runtime tunables come from the environment (or Compose-interpolated `.env`). Never commit real values. Template: [`.env.example`](../../.env.example).

Startup validation: `Settings.validate_runtime()` in `src/nova/config/__init__.py` (skipped when `APP_ENV` is `test` / `testing`).

## Compose / Postgres

| Variable | Required | Default / example | Purpose |
|----------|----------|-------------------|---------|
| `POSTGRES_USER` | Recommended | `nova` | DB role name |
| `POSTGRES_PASSWORD` | **Yes** (Compose) | placeholder in `.env.example` | DB password; replace before `compose up` |
| `POSTGRES_DB` | Recommended | `nova` | Database name |
| `POSTGRES_PORT` | No | `5432` | Host port published for Postgres |

Compose builds the API `DATABASE_URL` from these targeting hostname `db`. Do not point the API container at `127.0.0.1`.

## Ports

| Variable | Default | Purpose |
|----------|---------|---------|
| `API_PORT` | `8000` | Host → API `:8000` |
| `WEB_PORT` | `8080` | Host → web nginx `:8080` (unprivileged) |

Production-readiness smoke defaults (verify script): `API_PORT=18000`, `WEB_PORT=18080`, `POSTGRES_PORT=15432`.

## API runtime

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `APP_ENV` | Recommended | `local` | `local` / `production` / `test`. Production enables stricter checks |
| `LOG_LEVEL` | No | `INFO` | `DEBUG`…`CRITICAL` |
| `SERVICE_NAME` | No | `nova-api` | JSON log `service` field |
| `API_AUTH_TOKEN` | **Yes** outside test | — | Shared Bearer / `X-API-Key`. Non-placeholder; **≥ 24 chars in production** |
| `DATABASE_URL` | Host tools / non-Compose | Compose builds it | SQLAlchemy URL (`postgresql+psycopg://…`) |
| `DOCUMENT_STORAGE_PATH` | Recommended | `/var/lib/nova/documents` (Compose) | Local blob store root |
| `MAX_DOCUMENT_SIZE_BYTES` | No | `10485760` (10 MiB) | Upload size cap |
| `MAX_REQUEST_BODY_BYTES` | No | `12582912` (12 MiB) | Global `Content-Length` reject threshold; must be ≥ document max |
| `ALLOWED_MIME_TYPES` | No | `application/pdf,text/plain` | Comma-separated allow-list |
| `DATABASE_CONNECT_TIMEOUT_SECONDS` | No | `5` | libpq connect timeout |
| `DB_WAIT_SECONDS` | No | `60` | Entrypoint wait budget before migration |
| `CORS_ORIGINS` | Recommended | localhost Vite/UI origins | Comma-separated. **No `*` in production** |

## LLM

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `LLM_PROVIDER` | No | `mock` | `mock` (default) or vendor id |
| `LLM_MODEL` | No | empty | Model name when not mock |
| `LLM_API_KEY` | Production if not mock | empty | Provider key; **required in production when provider ≠ mock** |

## Frontend (Compose `web`)

| Variable | When | Purpose |
|----------|------|---------|
| `API_AUTH_TOKEN` | Runtime env on `web` | Written into `runtime-config.js` at start — **not** a Docker build-arg |
| `VITE_API_BASE_URL` | Build-arg (Compose: `""`) | Empty = same-origin `/v1` via nginx proxy |
| `VITE_API_AUTH_TOKEN` | Local Vite only (`frontend/.env`) | Build-time demo token; **must not** be baked into production images |

## Production gates (`APP_ENV=production` / `prod`)

When production mode is enabled, startup fails if:

- `API_AUTH_TOKEN` is missing, a known placeholder, or shorter than 24 characters
- `DATABASE_URL` contains weak markers (`nova:nova@`, `:password@`, `:replace-me@`, `:changeme@`)
- `CORS_ORIGINS` includes `*`
- `LLM_PROVIDER` is not `mock` and `LLM_API_KEY` is empty
- `MAX_REQUEST_BODY_BYTES` < `MAX_DOCUMENT_SIZE_BYTES`

## Never commit

API keys, LLM credentials, database passwords, tokens, private keys, or real customer documents.

## Related

- [local.md](./local.md) · [production.md](./production.md) · [frontend.md](./frontend.md)
- [../security/baseline.md](../security/baseline.md)
