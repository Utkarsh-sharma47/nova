# Problem statement

## Business problem

Trade and shipping operations depend on documents such as commercial invoices and Bills of Lading. Before a shipment can be trusted operationally, key fields must be checked against what the customer expects under their rules: parties, amounts, ports, dates, references, and other contractual constraints.

Today this verification is often manual: operations staff read emails and attachments, compare fields to customer checklists, and email shippers for corrections. The loop is slow, inconsistent, expensive, and hard to audit.

## Existing manual workflow

1. Shipper emails documents (or drops them in a shared channel).
2. Validation team opens attachments.
3. Staff visually extract fields and compare them to customer-specific rules.
4. On mismatch or ambiguity, staff email the shipper requesting amendments.
5. Revised documents arrive; steps 2–4 repeat.
6. Eventually a human marks the packet acceptable and processing continues.

Decisions live in inboxes and tribal knowledge rather than structured, queryable records.

## Pain points

- High labor cost per document set
- Inconsistent application of the same customer rules across reviewers
- Slow turnaround when amendment loops span days
- Weak audit trail — hard to prove why something was approved
- Fatigue errors on repetitive field checks
- Difficulty querying historical decisions (“why did we request an amendment last time?”)

## Why manual verification is expensive and error-prone

- Document layouts vary (clean PDFs vs scans, stamps, marks).
- Customer rules differ by account and change over time.
- Critical mismatches are sparse relative to volume — easy to miss under load.
- Email threads mix chatter with formal decisions.
- Rework after a missed mismatch costs far more than catching it early.

## Who is affected

| Role | Impact today |
|------|----------------|
| Validation / operations analyst | Time spent on repetitive extraction and email ping-pong |
| Operations lead | Unpredictable throughput; weak metrics |
| Account / rules owner | Rules applied inconsistently |
| Shipper (indirect) | Slow feedback on corrections |
| Downstream ops | Delays when bad documents slip through |

## What success looks like (problem → outcome)

Replace the manual email verification loop with a governed pipeline that:

- extracts fields with confidence and evidence
- applies customer rules consistently
- auto-approves only when justified
- routes risk to humans or amendment requests
- leaves an auditable, queryable record

## What must not be “solved” by blind automation

- Auto-approve under low confidence, weak evidence, or UNCERTAIN validation
- Inventing fields not grounded in the document
- Sending commercial outbound messages without Part 2 approval controls
- Overriding explicit customer rules via unconstrained LLM judgment

See also: [system-of-outcomes.md](./system-of-outcomes.md), requirements REQ-PROD-*.
