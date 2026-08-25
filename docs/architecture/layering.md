# Layering rules

## Allowed dependency direction

```text
Presentation → API → Application → Domain ← Infrastructure adapters
                         ↓
                    Persistence ports
```

Infrastructure implements ports defined by application/domain. Domain does not import FastAPI, SQLAlchemy engines, or vendor SDKs.

## Package map (target)

| Package | Contents | Phase |
|---------|----------|-------|
| `nova.contracts` | Pydantic I/O models | **2 (now)** |
| `nova.domain` | Pure policy helpers, enums | 3+ |
| `nova.agents` | Extractor / Validator / Router | 3–4 |
| `nova.application` | Use-cases / pipeline runner | 3+ |
| `nova.api` | FastAPI routers | 3+ |
| `nova.infra.*` | LLM, documents, DB, observability | 3–5 |

## Rules

1. API handlers call application services only.
2. Agents call `LLMPort` / repositories via injected ports.
3. Deterministic validation lives in domain code; LLM judgment isolated and labeled.
4. Persistence transactions owned by application services.
5. No circular imports between `agents` and `api`.
