# ADR-0005: AI provider abstraction

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-08-25 |
| Deciders | Principal Software Architect (Phase 2) |
| Supersedes | — |
| Superseded by | — |

## Context

### Problem

Agents may call LLMs. Binding domain code to one vendor creates lock-in and complicates testing.

### Requirements

- Provider-agnostic calls with timeouts, retries, token/cost accounting
- Structured outputs validated against Pydantic contracts
- Record model/prompt versions (`REQ-AI-006`)
- Never treat LLM output as trusted without schema validation

## Decision

Define an **`LLMPort`** used by agents:

```text
LLMPort.complete(request: LLMRequest) -> LLMResponse
```

- Adapters implement vendor SDKs; domain depends only on the port.
- **MockLLM** required for CI (no network).
- Prompt templates versioned (`prompt_id` + `prompt_version`).
- Concrete vendor for demos is environment configuration, not a domain freeze.

Agent trust rules: [ADR-0010](./0010-ai-agent-contracts-and-trust-model.md).

## Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| Hard-code OpenAI SDK in agents | Fastest demo | Lock-in; hard to mock |
| LangChain as core architecture | Batteries | Opaque graphs; harder audit |
| LlamaIndex-centric | Retrieval helpers | Verification ≠ RAG-first |
| Multi-provider fanout in Part 1 | Resilience | Ops complexity premature |

## Consequences

### Advantages

Swap providers without rewriting agents; MockLLM tests; clear cost metrics.

### Disadvantages

Thin abstraction; lowest-common-denominator features.

### Operational cost

One API key per configured provider.

### Complexity

Low if port stays small.

### Developer velocity

Slightly slower initially; much faster for testing.

### Testing implications

Unit tests never need real keys.

### Deployment implications

`LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY` via env.

### Part 2 compatibility

Draft-reply agent can reuse the same port.

### Migration risk

Low; vendor adapters localized.

## Compliance

- Validate LLM JSON against contracts before use.
- Failures map to `AIProviderError` / `AIOutputError`.
- Uncertainty must not become `AUTO_APPROVE`.

## References

- `REQ-AI-004`–`006`, `REQ-ROUTER-005`, `REQ-OBS-003`
