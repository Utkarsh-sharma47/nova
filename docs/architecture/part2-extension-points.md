# Part 2 extension points

Part 2 is **PLANNED — NOT IMPLEMENTED IN PART 1**. Part 1 must avoid designs that make these additions unnecessarily hard.

## Principles for extension

- Prefer **ports/adapters** over hard-wiring UI upload as the only possible source.
- Model **shipment 1→N documents** even if Part 1 only inserts one.
- Keep validation functions ready to accept a **document set context** later.
- Treat outbound communication as a separate adapter behind an interface.
- Persist decisions so **approval state** can be added without rewriting history.

## Extension map

| Part 2 capability | Part 1 status | Part 1 design obligation | Anti-pattern to avoid |
|-------------------|---------------|--------------------------|------------------------|
| Email ingestion | **PLANNED** | Define an ingestion port; UI is one adapter | Coupling pipeline entry to a single HTTP upload handler with no interface |
| File/attachment ingestion | **PLANNED** | Same ingestion port; attachment metadata fields reserved | Assuming exactly one blob forever with no document entity |
| Multiple documents per shipment | **PLANNED** (schema 1:N ready) | Schema: shipment has many documents | One table row that mixes shipment + single file blobs inseparably |
| Cross-document consistency | **PLANNED** | Validator accepts list/context of extractions | Validator signature that can never take more than one extraction |
| Draft replies | **PLANNED** | Communication draft interface; unused in Part 1 | Embedding email-send side effects inside router |
| Human approval | **PLANNED** | Decision record allows future approval transitions | Overwriting router decision without history |
| Outbound sending | **PLANNED** | Outbound adapter not required in Part 1; interface reserved | Auto-sending from Part 1 router path |

## Minimal interfaces (conceptual)

```text
IngestionPort.submit(source) -> DocumentRef
ValidationPort.validate(customer_rules, extractions[]) -> ValidationResult
CommunicationPort.draft(amendment_context) -> DraftMessage   # Part 2
CommunicationPort.send(draft_id, approval) -> SendResult     # Part 2
```

Exact signatures will be fixed in implementation ADRs; this file only preserves intent.

## What we deliberately do not build now

Queues for mail providers, full mailbox sync, multi-doc UI workflows, reply editors, approval permission matrices, SMTP/ESP integrations.
