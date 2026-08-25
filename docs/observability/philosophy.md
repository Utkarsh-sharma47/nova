# Observability philosophy

## Why

Trade verification decisions must be explainable after the fact. Logs and traces are part of the product’s auditability.

## Minimum viable observability (Part 1 implementation phases)

- **Run ID / correlation ID** on every stage log
- **Structured logs** (JSON or equivalent) with stage name, status, duration
- **Error taxonomy** codes for failures
- **Model metadata** (provider, model name, prompt version) on LLM calls
- **Token/cost counters** when available from the provider

## What not to log

- API keys and secrets
- Full document bodies in production default log levels (prefer hashes/refs; redaction policy in security docs)
- Raw customer credentials

## UI/query linkage

Operators should jump from a UI decision view to the run ID that produced it.
