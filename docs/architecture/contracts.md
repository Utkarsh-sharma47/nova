# Domain contracts

Authoritative runtime schemas: `src/nova/contracts/` (Pydantic). Narrative agent contracts also in [`docs/agents/contracts.md`](../agents/contracts.md).

## Versioning

Every message includes `contract_version` (semver). Additive optional fields = minor; breaking = major. Persisted payloads store the version used.

## Stage contracts

| Contract | Module |
|----------|--------|
| `ExtractionRequest` / `ExtractionResult` | `extraction.py` |
| `ValidationRequest` / `ValidationResult` | `validation.py` |
| `RoutingRequest` / `DecisionResult` | `routing.py` |
| `ErrorResponse` | `errors.py` |
| `AuditEvent` | `audit.py` |

Shared: confidence, evidence, uncertainty, trace IDs, document/shipment IDs — see [confidence-and-evidence.md](./confidence-and-evidence.md) and [error-model.md](./error-model.md).

## Testing

`tests/contracts/` validates schemas. No LLM calls.
