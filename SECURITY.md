# Security Policy

## Reporting a vulnerability

If you discover a security issue in Nova, do **not** open a public GitHub issue.

Email the repository maintainer(s) with:

- a clear description of the issue
- steps to reproduce (if applicable)
- impact assessment
- any suggested remediation

We will acknowledge receipt and work on a fix before any public disclosure.

## Secrets and credentials

Never commit secrets to this repository.

| Do commit | Do not commit |
|-----------|---------------|
| `.env.example` (placeholders only) | `.env`, `*.env`, real API keys |
| Documentation of required variables | Private keys (`.pem`, `.key`, etc.) |
| Public configuration samples | Cloud credential files, tokens, passwords |

Local secrets belong in a gitignored `.env` (see `.env.example`).

If a secret is accidentally committed:

1. Rotate/revoke the credential immediately.
2. Remove it from git history (coordinate with maintainers).
3. Treat the leaked value as compromised even after deletion from the latest commit.

## CI and automated checks

Phase 1 CI includes secret-pattern scanning and Gitleaks on pull requests and pushes to `main`. These reduce accidental leaks; they do not replace careful review.

## Scope note

Application authentication, document storage, and PII handling policies will be documented under `docs/security/` as those systems are implemented. Until then, treat all customer and shipping document data as sensitive.
