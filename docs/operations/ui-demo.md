# Part 1 UI demo flow (synthetic fixtures only)

This runbook demonstrates the Phase 9 operations UI against a local Nova stack.
It uses **synthetic** invoice text only. Do not claim real customer-document performance.

## Prerequisites

1. Copy `.env.example` → `.env` and set a non-placeholder `API_AUTH_TOKEN`.
2. Start the stack:

```bash
docker compose up --build
```

- API: `http://localhost:8000`
- UI: `http://localhost:8080`

For Vite local development (API already running):

```bash
cd frontend
cp .env.example .env
# set VITE_API_AUTH_TOKEN to the same token as the API
npm install
npm run dev
```

## Flow

1. Open the UI dashboard.
2. Click **Create demo customer** (calls `POST /v1/customers`) and note the UUID.
3. Go to **Upload**.
4. Select `fixtures/demo/synthetic_invoice.txt` (`text/plain`).
5. Confirm customer UUID is filled (session storage), set document type `INVOICE`, upload.
6. Wait for `202 Accepted` and open the document detail link.
7. Observe lifecycle progression toward `DECIDED` or `FAILED` (MockLLM pipeline).
8. Inspect extraction fields (confidence / presence / evidence), validation checks, and decision.
   - Treat `HUMAN_REVIEW` and `UNCERTAIN` as first-class outcomes.
   - Never assume `AUTO_APPROVE` unless the decision API returns it.
9. Open the linked shipment detail.
10. On **Query**, ask a supported question, for example:
    - `What is the decision for this document?` with document id in scope
    - `Which shipments are in HUMAN_REVIEW?`
11. Also try an unsupported question (future ETA prediction) and confirm `UNSUPPORTED`.

## Curl equivalent (optional)

```bash
TOKEN="$API_AUTH_TOKEN"
BASE=http://localhost:8000

CUSTOMER=$(curl -sS -X POST "$BASE/v1/customers" \
  -H "X-API-Key: $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Demo Customer"}' | python -c 'import sys,json; print(json.load(sys.stdin)["customer_id"])')

curl -sS -X POST "$BASE/v1/documents" \
  -H "X-API-Key: $TOKEN" \
  -H "Idempotency-Key: demo-invoice-001" \
  -F "customer_id=$CUSTOMER" \
  -F "document_type=INVOICE" \
  -F "file=@fixtures/demo/synthetic_invoice.txt;type=text/plain"
```

## Notes

- Dashboard totals come from `GET /v1/ops/summary` — never frontend mocks.
- Query answers are grounded allow-listed intents only (`POST /v1/query`).
- Failures should surface `trace_id` in the technical error panel for log correlation.
