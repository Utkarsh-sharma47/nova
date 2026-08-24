# Observability architecture

Extends [philosophy.md](./philosophy.md). ADR: [0007](../decisions/0007-observability.md).

## Identifiers

| ID | Scope |
|----|-------|
| `request_id` | Inbound HTTP request |
| `trace_id` | Full verification run (Part 1 correlation) |
| `agent_execution_id` | One agent invocation |

## Structured log fields (minimum)

`timestamp`, `level`, `message`, `trace_id`, `request_id`, `agent_execution_id`, `shipment_id`, `document_id`, `stage`, `status`, `duration_ms`, `error_code`.

## Metrics (define now; implement with agents)

`nova_request_latency_seconds`, `nova_agent_latency_seconds`, `nova_llm_latency_seconds`, `nova_llm_failures_total`, `nova_llm_tokens_total`, `nova_llm_estimated_cost_usd_total`, `nova_validation_outcomes_total`, `nova_routing_outcomes_total`, `nova_retry_count_total`, plus derived human-review rate.

## Health

`/health` liveness; `/ready` DB + config.
