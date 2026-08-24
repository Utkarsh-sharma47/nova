# Problem definition

## 1. Business problem

Trade and shipping operations depend on documents such as commercial invoices and Bills of Lading. Before a shipment can be trusted operationally, key fields must be checked against what the customer (consignee/shipper/forwarder policy) expects: parties, amounts, ports, dates, references, and other contractual constraints.

Today this verification is often done manually by operations teams reading emails and attachments, comparing fields to customer rules, and emailing shippers for corrections. That process is slow, inconsistent, and hard to audit.

## 2. Existing manual workflow

Typical loop:

1. Shipper emails documents (or uploads to a shared channel).
2. Validation team opens attachments.
3. Staff visually extract fields and compare to customer-specific checklists/rules.
4. On mismatch or ambiguity, staff email the shipper asking for amendments.
5. Revised documents arrive; steps 2–4 repeat.
6. Eventually a human marks the packet acceptable and processing continues.

Decisions live in inboxes and tribal knowledge rather than structured systems.

## 3. Pain points

- High labor cost per document set
- Inconsistent application of the same customer rules across reviewers
- Slow turnaround when amendment loops span days
- Weak audit trail: hard to prove why something was approved
- Fatigue errors on repetitive field checks
- Difficulty querying historical decisions ("why did we request amendment last time?")

## 4. Why manual verification is expensive and error-prone

- Documents vary in layout quality (clean PDFs vs scans, stamps, handwritten marks).
- Customer rules differ by account and change over time.
- Critical mismatches are sparse relative to volume — easy to miss under load.
- Email threads mix operational chatter with formal decisions.
- Re-work after a missed mismatch is far more expensive than catching it early.

## 5. Who uses Nova

| Role | Need |
|------|------|
| Validation / operations analyst | Review uncertain cases, see evidence, act on queue |
| Operations lead | Monitor throughput, mismatches, amendment rates |
| Customer success / account ops | Ensure customer-specific rules are applied |
| Shipper (indirect, Part 2+) | Receives amendment requests / drafts |
| Engineer / evaluator | Inspect traces, eval quality, failure modes |

## 6. What Nova automates

- Field extraction from supported trade documents
- Attachment of confidence and evidence to extracted fields
- Application of customer-specific validation rules
- Structured MATCH / MISMATCH / UNCERTAIN outcomes
- Disposition routing: AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST
- Persistence and query (including natural-language query over stored records)
- Minimal operations UI for B2B review

## 7. What Nova must NOT automate blindly

- Auto-approve when confidence is low or evidence is weak
- Auto-approve when validation is UNCERTAIN or rules cannot be evaluated
- Silent invention of fields not grounded in the document
- Sending outbound commercial emails without Part 2 approval controls
- Overriding explicit customer rules via unconstrained LLM judgment

## 8. Where human review remains necessary

- Low-confidence extractions
- Conflicting or incomplete evidence
- Novel document layouts outside eval coverage
- Policy edge cases and high-value / high-risk shipments
- Customer rule ambiguity
- Any Part 2 outbound communication approval

## 9. Desired operational outcome

A measurable reduction in manual touch time per document, with a clear audit trail, consistent rule application, and safe routing of risk to humans — so operations can auto-approve only when justified and spend human attention where it matters.
