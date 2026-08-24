# API versioning

Part 1 versioning strategy for Nova’s public HTTP API. Goal: predictable evolution without unnecessary ceremony.

## Strategy

**URL path versioning** with a major version prefix:

```text
/v1/...
```

Examples: `/v1/documents`, `/v1/shipments/{shipment_id}`, `/v1/query`.

### Why path versioning

- Explicit in docs, OpenAPI, and client code
- Easy to route and to sunset
- Matches FastAPI router mounting ([ADR-0004](../decisions/0004-api-framework.md))

### What we deliberately avoid (Part 1)

| Approach | Why not now |
|----------|-------------|
| Header-only versioning | Harder to discover; easy to misconfigure |
| Per-endpoint micro-versions | Noise for a small surface |
| GraphQL schema versioning | REST is the Part 1 surface |
| Date-based versions | Overkill for assignment/demo cadence |

## Compatibility rules

Within `/v1`:

| Change type | Allowed without `/v2`? | Notes |
|-------------|------------------------|-------|
| Add optional response field | Yes | Clients ignore unknown fields |
| Add optional request field | Yes | Server defaults when absent |
| Add new endpoint | Yes | |
| Add enum value (documented) | Prefer additive carefully | Clients should tolerate unknown enums where forward-compatible |
| Rename/remove field | No | Requires `/v2` or coordinated deprecation |
| Change field meaning / type | No | Breaking → `/v2` |
| Change auth scheme incompatibly | No | `/v2` or dual-run period |

## Unversioned operational endpoints

Liveness and readiness stay **outside** `/v1` so orchestrators do not need API-version knowledge:

| Path | Purpose |
|------|---------|
| `GET /health` | Process liveness |
| `GET /ready` | Dependency readiness |

See [contracts.md](./contracts.md).

## Media types

- Request/response: `application/json` unless multipart upload (`multipart/form-data` for ingestion).
- Optional future: `application/vnd.nova.v1+json` is **not** required for Part 1.

## Deprecation

When `/v2` is introduced:

1. Document differences in `docs/api/`.
2. Keep `/v1` until a stated sunset date.
3. Return `Deprecation` / `Sunset` headers on `/v1` once sunset is scheduled (implementation phase).

## Contract vs HTTP version

- **HTTP `/v1`**: external API wire format.
- **Agent/domain contract versions**: internal Pydantic/schema versions (agent docs / `nova.contracts`). They may evolve on a different cadence but must remain mappable to `/v1` responses.

## Related

- [contracts.md](./contracts.md)
- [error-model.md](./error-model.md)
- [ADR-0004](../decisions/0004-api-framework.md)
