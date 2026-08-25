# Security architecture

Extends [baseline.md](./baseline.md). Phase 11 hardens deploy-time controls without redesigning Part 1 auth.

## Secret management

- Env / secret store only; `.env` gitignored (`REQ-SEC-001`, `REQ-SEC-005`).
- **Secrets must not appear in image layers.** API tokens for the ops UI are injected at **container start** into `runtime-config.js` (`window.__NOVA_RUNTIME__`), not via Vite build-args.
- Lockfiles: `package-lock.json`; Python deps pinned via `pyproject.toml` / install in image builder stage.
- CI secret pattern scan: `scripts/check-secret-patterns.sh`.

## API authentication (Part 1)

Shared API key / Bearer for demo operators. All non-health routes require auth (`Authorization: Bearer` or `X-API-Key`). Fine-grained RBAC deferred.

Production startup rejects missing, placeholder, or short (`< 24`) tokens when `APP_ENV=production`.

## CORS

`CORS_ORIGINS` is an explicit allow-list (Vite + Compose UI origins by default). Credentials are not enabled. **Wildcard `*` is rejected in production.**

## Containers

| Control | Implementation |
|---------|----------------|
| Non-root API | UID/GID 10001 |
| Non-root web | `nginxinc/nginx-unprivileged`, port 8080 |
| No secrets in images | Runtime env for `API_AUTH_TOKEN` on `web` |
| Healthchecks | `/health`, `/ready` (API); wget `/` (web) |
| Signal handling | SIGTERM (API), SIGQUIT (web) |

## Request and upload limits

| Control | Config / code |
|---------|----------------|
| Document size | `MAX_DOCUMENT_SIZE_BYTES` (default 10 MiB) |
| Request body | `MAX_REQUEST_BODY_BYTES` (default 12 MiB) + early `Content-Length` middleware |
| MIME allow-list | `ALLOWED_MIME_TYPES` (`application/pdf`, `text/plain`) |
| Path safety | Storage confinement under `DOCUMENT_STORAGE_PATH` |
| Nginx body | `client_max_body_size` aligned with API (~12m) |

See [baseline.md](./baseline.md) for upload control status.

## Authorization

Operator: ingest + read + NL query. System: pipeline writes + audit. Anonymous: health/ready/metrics only. Filter by `customer_id` when richer auth lands.

## Documents

Store URI + hash in DB; scrubbed fixtures only; malware scanning remains environment-dependent.

## Logging / PII

Prefer IDs; redact Authorization and secret-like keys; avoid full commercial fields at INFO. Safe API errors expose `trace_id` + stable codes — not stack traces.

## Prompt injection & malicious docs

Document text is untrusted; extract/validate only; NL query grounded on DB ([query-api.md](./query-api.md)); timeouts; fail toward `HUMAN_REVIEW` on crashes.

## LLM output

Pydantic validation mandatory; never execute model-suggested code.

## Dependencies

Pin versions; CI `pip-audit` / `npm audit` visibility; prefer official SDKs.
