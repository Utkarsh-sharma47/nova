# Security baseline

## Repository rules (Phase 1 — enforced)

- `.env` and variants are gitignored; `.env.example` is allowed **without real secrets**
- No API keys, tokens, passwords, or private keys in source, docs, tests, or CI logs
- Secret pattern scanning runs in CI (`scripts/check-secret-patterns.sh`)
- Never commit customer documents that contain real PII/commercial secrets; use scrubbed fixtures

## Logging policy

- Do not log secrets
- Prefer document IDs/hashes over full payloads at info level
- Redact authorization headers and provider API keys in error reports

## Dependencies (when introduced)

- Use lockfiles (`package-lock.json`, `poetry.lock`, `uv.lock`, etc.)
- Pin direct dependencies; review transitive upgrades intentionally
- Prefer official/trusted packages; avoid copy-pasted credential helpers

## Document upload security (deferred)

Address in implementation phases before exposing public upload:

- File type allow-lists
- Size limits
- Content sniffing vs extension trust
- Storage isolation
- Malware scanning strategy as appropriate for the deploy environment

Tracked as `REQ-SEC-004` (deferred).

## Human process

- Rotate any key that accidentally leaks
- Treat assignment LLM provider keys as secrets even in personal forks
