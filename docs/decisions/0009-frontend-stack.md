# ADR-0009: Frontend stack (React, TypeScript, Vite)

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-08-25 |
| Deciders | Principal Software Architect (Phase 2) |
| Supersedes | — |
| Superseded by | — |

## Context

### Problem

Part 1 requires a minimal B2B operations UI (`REQ-UI-001`–`003`).

### Requirements

- Typed client against OpenAPI/contracts
- Modest SPA complexity
- Separate from backend optionally
- No Part 2 approval workflows required yet

## Decision

Use **React + TypeScript + Vite** (implementation in Phase 6). Phase 2 delivers stack decision + docs only.

## Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| Server-rendered Django/Jinja | Fewer moving parts | Couples UI to backend |
| Next.js | SSR/routing | Extra complexity for internal ops UI |
| Vue / Svelte | Fine DX | Smaller shared familiarity vs React here |
| No UI (API only) | Faster | Fails `REQ-UI-001` |

## Consequences

### Advantages

Clear separation from API; strong typing; fast Vite DX.

### Disadvantages

Second toolchain (Node) in the repo.

### Operational cost

Static hosting or nginx container; low.

### Complexity

Low for minimal pages.

### Developer velocity

High for standard React patterns.

### Testing implications

UI smoke deferred until UI exists.

### Deployment implications

Build `dist/` into image or object storage.

### Part 2 compatibility

Approval actions and reply drafts become additional pages.

### Migration risk

Low if API contracts remain stable.

## Compliance

- Do not implement UI in Phase 2.
- When implemented, surface evidence/confidence per `REQ-UI-002`.

## References

- `REQ-UI-001`–`003`
- [`docs/api/`](../api/)
