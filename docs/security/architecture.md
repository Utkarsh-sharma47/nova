# Security architecture

Extends [baseline.md](./baseline.md).

## Secret management

Env / secret store only; `.env` gitignored; lockfiles when deps land (`REQ-SEC-005`).

## API authentication (Part 1)

Shared API key or bearer for demo operators. All non-health routes require auth. Fine-grained RBAC deferred.

## Authorization

Operator: ingest + read + NL query. System: pipeline writes + audit. Anonymous: health/ready only. Filter by `customer_id` when auth lands.

## Documents

MIME allow-list, size limits, store URI+hash in DB, scrubbed fixtures only, malware strategy env-dependent (`REQ-SEC-004`).

## Logging / PII

Prefer IDs; redact Authorization; avoid full commercial fields at INFO.

## Prompt injection & malicious docs

Document text untrusted; extract/validate only; NL query grounded on DB; processor timeouts; fail to HUMAN_REVIEW on crashes.

## LLM output

Pydantic validation mandatory; never execute model-suggested code.

## Dependencies

Pin versions; prefer official SDKs; continue CI secret scan.
