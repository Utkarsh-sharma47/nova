# Security baseline

## Repository rules (enforced)

- `.env` and variants are gitignored; `.env.example` is allowed **without real secrets**
- No API keys, tokens, passwords, or private keys in source, docs, tests, or CI logs
- Secret pattern scanning runs in CI (`scripts/check-secret-patterns.sh`)
- Never commit customer documents that contain real PII/commercial secrets; use scrubbed fixtures

## Logging policy

- Do not log secrets
- Prefer document IDs/hashes over full payloads at info level
- Redact authorization headers and provider API keys in error reports
- JSON formatter redacts keys whose names contain fragments such as `authorization`, `api_key`, `password`, `secret`, `token`, `cookie`

## Dependencies

- Use lockfiles (`package-lock.json`; Python install from `pyproject.toml` in images)
- Pin direct dependencies; review transitive upgrades intentionally
- Prefer official/trusted packages; avoid copy-pasted credential helpers
- CI surfaces `pip-audit` and `npm audit` (high+) findings

## Document upload security (implemented — Phase 3 / hardened Phase 11)

| Control | Status |
|---------|--------|
| File type allow-list (`ALLOWED_MIME_TYPES`) | **Implemented** |
| Size limits (`MAX_DOCUMENT_SIZE_BYTES`) | **Implemented** |
| Global request body limit (`MAX_REQUEST_BODY_BYTES`) | **Implemented** (Phase 11) |
| Content sniffing vs claimed type | **Implemented** in ingestion processors |
| Storage isolation under configured root | **Implemented** (path-safe local storage) |
| Malware scanning strategy | **Deferred** — environment-dependent; not claimed for Part 1 Compose |

Tracked as `REQ-SEC-004` (upload controls delivered; malware scanning remains explicit backlog).

## Human process

- Rotate any key that accidentally leaks (including tokens previously baked into an image)
- Treat assignment LLM provider keys as secrets even in personal forks

## Related

- [architecture.md](./architecture.md)
- [query-api.md](./query-api.md)
- [../deployment/configuration.md](../deployment/configuration.md)
