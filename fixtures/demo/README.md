# Demo fixtures (synthetic only)

Checked-in samples for Part 1 demo and evaluation. **No real customer documents or PII.**

| File | Role |
|------|------|
| `synthetic_invoice.txt` | Default UI demo invoice |
| `synthetic_invoice_clean.txt` | Clean invoice matching demo control-group expected values |
| `synthetic_invoice_rejected.txt` | Rejected invoice with deliberate field mismatches vs control group |
| `synthetic_invoice_messy.txt` | Messy / adversarial invoice (ambiguity + prompt injection noise) |
| `synthetic_bol_clean.txt` | Clean Bill of Lading sample |

Use with the demo runbook: [`docs/operations/demo-runbook.md`](../../docs/operations/demo-runbook.md).

Demo customers created via `POST /v1/customers` are seeded with control-group `expected_fields` aligned to `synthetic_invoice_clean.txt`. Validation compares extracted values to those expectations (`equals.*` rules); mismatches must not AUTO_APPROVE.
