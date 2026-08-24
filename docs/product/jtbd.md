# Jobs to be done (JTBD)

Jobs are framed as operational outcomes for trade-document verification — not as “use an LLM.”

## Core jobs (Part 1)

### JTBD-01 — Verify a document against customer rules

**When** a trade document arrives for a shipment,  
**I want to** extract the required fields and check them against that customer’s rules,  
**so I can** decide whether the document is acceptable without re-reading the entire file by hand.

Maps to: REQ-EXT-*, REQ-VAL-*, REQ-AI-001–002

### JTBD-02 — Trust (or distrust) extracted values

**When** fields are machine-extracted,  
**I want to** see confidence and evidence for each field,  
**so I can** spend human attention only where the system is unsure or ungrounded.

Maps to: REQ-EXT-003–004, REQ-UI-002, REQ-AI-004

### JTBD-03 — Route work safely

**When** validation completes,  
**I want** a clear disposition — auto-approve, human review, or amendment request —  
**so we** do not block clean documents or silently pass risky ones.

Maps to: REQ-ROUTER-*, REQ-PROD-003–004

### JTBD-04 — Reconstruct why a decision happened

**When** someone questions an approval or amendment,  
**I want** persisted extraction, validation, and decision records,  
**so I can** audit and explain the outcome.

Maps to: REQ-DATA-001, REQ-VAL-006, REQ-OBS-002

### JTBD-05 — Ask operational questions without SQL

**When** I need status or history,  
**I want to** query persisted verification data in natural language (and structured APIs),  
**so I can** answer “what happened?” without inventing facts.

Maps to: REQ-QUERY-001–003

### JTBD-06 — Demo and evaluate quality honestly

**When** we claim the system works,  
**I want** clean and messy samples with reproducible evaluation and a failure path,  
**so reviewers** can verify behavior rather than trust slides.

Maps to: REQ-EXT-005, REQ-SUBMISSION-*, REQ-TEST-*

## Deferred jobs (Part 2 only)

| ID | Job | REQ |
|----|-----|-----|
| JTBD-P2-01 | Ingest from email/attachments without manual upload | REQ-PART2-001–002 |
| JTBD-P2-02 | Validate consistency across multiple documents in a shipment | REQ-PART2-003–004 |
| JTBD-P2-03 | Draft and send amendment communications with approval | REQ-PART2-005–007 |

These jobs must **not** be treated as Part 1 acceptance criteria.
