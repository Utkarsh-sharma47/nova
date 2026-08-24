# Agent documentation template

Copy this file when documenting a pipeline agent. Remove sections that are truly N/A only after noting why. Do not invent tools or model providers that are not decided.

---

# Agent: \<Name\>

| Field | Value |
|-------|-------|
| Status | Proposed / Active / Deprecated |
| Owner | |
| Last updated | YYYY-MM-DD |
| Related ADR(s) | |
| Related feature(s) | |

## 1. Purpose

What this agent is responsible for, and what it explicitly does **not** do.

## 2. Inputs

- Required inputs (schema or fields)
- Optional inputs
- Preconditions

## 3. Outputs

- Success output contract
- Partial / uncertain output handling
- Error output contract

## 4. Behavior

High-level behavior and decision rules. Avoid undecided implementation details.

## 5. Dependencies

- Upstream agents or services
- Downstream consumers
- External systems (only if decided)

## 6. Failure modes

| Failure | Detection | Handling |
|---------|-----------|----------|
| | | |

## 7. Security and data handling

Sensitive fields, redaction, and access constraints.

## 8. Testing

Unit/contract tests that cover this agent.

## 9. Evaluation

Quality metrics and fixtures relevant to this agent.

## 10. Observability

Logs, traces, and metrics that must exist for debugging decisions.

## 11. Known limitations

## 12. Change history

| Date | Change | Author |
|------|--------|--------|
| | | |
