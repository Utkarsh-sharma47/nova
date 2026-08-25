# Query API security

Normative controls for `POST /v1/query` (`REQ-QUERY-002`, `REQ-SEC-*`).

## Non-negotiable rule

The query layer **never** turns user text (or LLM output) into unrestricted database execution.

## Controls

| Threat | Control |
|--------|---------|
| SQL injection in question text | Security gate regex + never interpolate question into SQL |
| Arbitrary SQL / “run this query” | Rejected as `SECURITY_REJECTED` |
| Schema / catalog discovery | Rejected as `SECURITY_REJECTED` |
| Prompt injection / system prompt extraction | Rejected as `SECURITY_REJECTED` |
| Invented executable intents | Allow-list validation; unknown names → `UNSUPPORTED` |
| Cross-customer reads | Every repository method filters by `customer_id` |
| LLM inventing field values | Answers built only from repository rows |
| Mutating NL commands | `OUT_OF_SCOPE` / unsupported |

## Logging

Log intent name, status, customer_id, trace_id, latency. Do not log document bodies, API keys, or connection strings.

## Tests

`tests/query/test_query_security.py` and failure cases in `tests/query/test_query_failures.py`.

## Related

- [baseline.md](./baseline.md)
- [../api/query-interface.md](../api/query-interface.md)
