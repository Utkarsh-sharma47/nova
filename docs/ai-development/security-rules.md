# Security rules for AI-assisted development

Security constraints for AI coding agents working on Nova.

## Non-negotiable

AI coding agents must never:

- Commit secrets, API keys, tokens, private keys, or production credentials.
- Hardcode production credentials in source, tests, fixtures, docs, or examples.
- Bypass CI security checks or secret scanning.
- Log raw secrets or unnecessary sensitive document contents.
- Weaken authentication, authorization, or validation controls to pass a test.
- Introduce unsafe deserialization, command injection, or unrestricted file access patterns.

## Secrets handling

- Use environment variables or a secrets manager; never commit `.env` files with real values.
- Example configs must use obvious placeholders only.
- If a secret is accidentally committed, stop, rotate the secret, and follow incident guidance in `docs/security/` / `SECURITY.md` (do not rewrite history unless explicitly authorized).

## Document and PII data

Trade documents may contain sensitive commercial and personal data.

Agents must:

- Minimize persistence and logging of document contents to what operations require.
- Avoid copying production documents into the repository.
- Prefer synthetic or redacted fixtures for tests and evaluation.
- Treat uploads and extracted fields as sensitive by default.

## AI / model security

- Do not send secrets in prompts.
- Bound tool permissions for any agent that can call tools or write data.
- Treat model output as untrusted input to downstream systems; validate against schemas.
- Never allow model output alone to grant `AUTO_APPROVE` when policy requires human review.

## Dependency and supply chain

- Prefer pinned, reviewed dependencies.
- Do not add packages from untrusted sources.
- Avoid downloading and executing remote scripts as part of a change unless explicitly required and reviewed.

## Related documents

- [`coding-rules.md`](./coding-rules.md)
- [`git-rules.md`](./git-rules.md)
- [`review-checklist.md`](./review-checklist.md)
- Root [`SECURITY.md`](../../SECURITY.md) (when present)
- `docs/security/`
