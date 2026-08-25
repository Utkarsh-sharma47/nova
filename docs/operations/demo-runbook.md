# Part 1 demo runbook (submission)

Reproducible walkthrough for reviewers. Uses **synthetic fixtures only** — no real customer documents or PII.

Companion UI notes: [ui-demo.md](./ui-demo.md).

## 1. Start Nova

```bash
cp .env.example .env
# set a long non-placeholder API_AUTH_TOKEN and POSTGRES_PASSWORD
docker compose up --build
```

| Surface | URL |
|---------|-----|
| API | http://localhost:8000 |
| UI | http://localhost:8080 |
| Health | `curl http://localhost:8000/health` |
| Ready | `curl http://localhost:8000/ready` |

Wait until `/ready` returns ready and the UI loads.

## 2. Upload a synthetic invoice (happy / clean path)

**UI**

1. Open the dashboard → **Create demo customer** (records the customer UUID).
2. **Upload** → select `fixtures/demo/synthetic_invoice_clean.txt` (`text/plain`).
3. Document type: `INVOICE` → upload.
4. Follow the document link from the `202 Accepted` response.

**API**

```bash
TOKEN="$API_AUTH_TOKEN"
BASE=http://localhost:8000

CUSTOMER=$(curl -sS -X POST "$BASE/v1/customers" \
  -H "X-API-Key: $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Demo Customer"}' | python -c 'import sys,json; print(json.load(sys.stdin)["customer_id"])')

curl -sS -X POST "$BASE/v1/documents" \
  -H "X-API-Key: $TOKEN" \
  -H "Idempotency-Key: demo-clean-invoice-001" \
  -F "customer_id=$CUSTOMER" \
  -F "document_type=INVOICE" \
  -F "file=@fixtures/demo/synthetic_invoice_clean.txt;type=text/plain"
```

## 3. Observe processing

On the document detail page, refresh until lifecycle reaches `DECIDED` or `FAILED` (MockLLM pipeline by default). Correlation IDs (`trace_id` / request headers) appear on errors for log lookup.

## 4. Inspect extracted fields

Confirm each field shows:

- value or explicit presence (`MISSING` / `AMBIGUOUS` / etc. when applicable)
- confidence
- evidence / grounding snippet

Do not treat UI placeholders as business data — values come from `GET /v1/documents/{id}`.

## 5. Inspect validation

Open validation on the same page (or `GET /v1/documents/{id}/validation`). Expect one of:

- `MATCH`
- `MISMATCH`
- `UNCERTAIN`

with per-check reasons / rule identifiers.

## 6. Inspect decision

Open decision (`GET /v1/documents/{id}/decision`). Expect one of:

- `AUTO_APPROVE`
- `HUMAN_REVIEW`
- `AMENDMENT_REQUEST`

Never assume `AUTO_APPROVE` unless the API returns it. Fail-closed paths prefer `HUMAN_REVIEW`.

## 7. Query the shipment / document

On **Query**, try:

- `What is the decision for this document?` (include document id in scope / question as the UI requires)
- `Which shipments are in HUMAN_REVIEW?`

Then try an unsupported or injection-like question and confirm a safe refusal (`UNSUPPORTED`), not invented SQL or fabricated facts.

## 8. Demonstrate a failure-safe / HUMAN_REVIEW case

Upload `fixtures/demo/synthetic_invoice_messy.txt` with a new `Idempotency-Key`.

Expected reviewer observation:

- extraction may mark ambiguity / low confidence / missing fields
- validation may be `UNCERTAIN` or `MISMATCH`
- decision should **not** silently become unsafe `AUTO_APPROVE`

Optional Bill of Lading sample: `fixtures/demo/synthetic_bol_clean.txt` with document type `BILL_OF_LADING` (or the enum value accepted by the API).

## 9. Optional evaluation proof

```bash
PYTHONPATH=src python scripts/run_full_evaluation.py
# gate: false AUTO_APPROVE count must be 0
```

Reports land under `docs/evaluation/reports/`.

## Notes

- Dashboard totals use `GET /v1/ops/summary` (real aggregates).
- Default LLM is MockLLM; live vendor adapters are optional and not required for Part 1 demo.
- Remote production deploy is **NOT EXECUTED** in this repository’s audit evidence.
