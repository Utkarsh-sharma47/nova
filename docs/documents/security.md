# Document processing security controls

| Threat | Control |
|--------|---------|
| Path traversal in filenames | Basename-only sanitization; reject `..` / null bytes |
| Path traversal in storage URIs | Scheme allow-list + resolve-under-root checks |
| Oversized uploads | `DocumentLimits.max_bytes` |
| Extension spoofing | Magic-byte MIME detection + mismatch rejection |
| Corrupt / truncated PDFs | Header + EOF checks; parser error → `DOC_CORRUPT` |
| PDF object / decompression bombs | Max pages + max PDF object count |
| Malicious content execution | Bytes never executed; text treated as untrusted |
| PII in logs | Log IDs, sizes, status, duration — **never** document bodies |

Related: `REQ-SEC-004`, `docs/security/architecture.md`.
