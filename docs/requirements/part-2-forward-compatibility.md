# Part 2 — forward compatibility only

**Do not implement Part 2 product features in Part 1.**

This document captures architectural obligations so Part 1 does not paint the system into a corner. Requirements here are **extension-point requirements**, not delivery scope for the current assignment part.

## Principles

1. Prefer ports/interfaces over hard-wired single-channel ingestion.
2. Keep shipment → documents as **1:N** even if Part 1 uses one document.
3. Keep validation stage able to accept a **multi-document context** later.
4. Keep communication (draft/send) behind a **port** unused in Part 1.
5. Keep decision records able to grow **approval state transitions** later.
6. Do not over-engineer: define extension points, not full Part 2 systems.

---

## REQ-PART2 cards

### REQ-PART2-001

| Field | Value |
|-------|-------|
| **ID** | REQ-PART2-001 |
| **Description** | Preserve an extension point for **email ingestion triggers**. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P2 |
| **Scope** | Part 2 |
| **Acceptance criteria** | Architecture documents an ingestion port; Part 1 input is one adapter behind that port (or equivalent seam). |
| **Implementation phase** | Design in 1–2; feature in Part 2 |
| **Test strategy** | Design review only in Part 1 |
| **Evidence** | Extension-points design doc |
| **Status** | documented |

### REQ-PART2-002

| Field | Value |
|-------|-------|
| **ID** | REQ-PART2-002 |
| **Description** | Preserve an extension point for **file/attachment ingestion** from multiple sources. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P2 |
| **Scope** | Part 2 |
| **Acceptance criteria** | Ingestion interface allows additional sources without rewriting core pipeline stages. |
| **Implementation phase** | Design in 1–2; feature in Part 2 |
| **Test strategy** | Design review only in Part 1 |
| **Evidence** | Extension-points design doc |
| **Status** | documented |

### REQ-PART2-003

| Field | Value |
|-------|-------|
| **ID** | REQ-PART2-003 |
| **Description** | Support **multiple documents per shipment** later. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P2 |
| **Scope** | Part 2 |
| **Acceptance criteria** | Data model is 1:N shipment→document (see also REQ-DATA-002). |
| **Implementation phase** | Schema in 2–5; multi-doc workflows in Part 2 |
| **Test strategy** | Schema review in Part 1; E2E in Part 2 |
| **Evidence** | ERD / database docs |
| **Status** | planned |

### REQ-PART2-004

| Field | Value |
|-------|-------|
| **ID** | REQ-PART2-004 |
| **Description** | Enable **cross-document consistency validation** later. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P2 |
| **Scope** | Part 2 |
| **Acceptance criteria** | Validation stage design can accept multi-document context without replacing MATCH/MISMATCH/UNCERTAIN semantics. |
| **Implementation phase** | Design in 1–4; feature in Part 2 |
| **Test strategy** | Design review only in Part 1 |
| **Evidence** | Extension-points / validator design |
| **Status** | documented |

### REQ-PART2-005

| Field | Value |
|-------|-------|
| **ID** | REQ-PART2-005 |
| **Description** | Enable **draft reply** generation later. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P2 |
| **Scope** | Part 2 |
| **Acceptance criteria** | A communication/draft port is defined and unused (or stubbed) in Part 1. |
| **Implementation phase** | Design in 1–2; feature in Part 2 |
| **Test strategy** | Design review only in Part 1 |
| **Evidence** | Extension-points design doc |
| **Status** | documented |

### REQ-PART2-006

| Field | Value |
|-------|-------|
| **ID** | REQ-PART2-006 |
| **Description** | Enable **human approval** workflow later. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P2 |
| **Scope** | Part 2 |
| **Acceptance criteria** | Decision records can accommodate later approval state transitions without changing Part 1 decision enum meaning. |
| **Implementation phase** | Design in 1–5; feature in Part 2 |
| **Test strategy** | Design review only in Part 1 |
| **Evidence** | Extension-points design doc; decision schema notes |
| **Status** | documented |

### REQ-PART2-007

| Field | Value |
|-------|-------|
| **ID** | REQ-PART2-007 |
| **Description** | Enable **outbound sending workflows** later. |
| **Source** | ASSIGNMENT REQUIREMENT |
| **Priority** | P2 |
| **Scope** | Part 2 |
| **Acceptance criteria** | Outbound adapter is not required in Part 1; interface reserved. |
| **Implementation phase** | Design in 1–2; feature in Part 2 |
| **Test strategy** | Design review only in Part 1 |
| **Evidence** | Extension-points design doc |
| **Status** | documented |

---

## Part 1 vs Part 2 boundary (summary)

| Concern | Part 1 | Part 2 |
|---------|--------|--------|
| Ingestion | Simple document input | Email + multi-source attachments |
| Documents per shipment | Typically one in demos | Many, with workflows |
| Validation | Single-document vs customer rules | Cross-document consistency |
| Communication | Disposition only (`AMENDMENT_REQUEST` as decision) | Draft replies + sending |
| Humans | Review visibility | Approval actions |

## Anti-patterns (forbidden in Part 1)

- Implementing email bots, send pipelines, or multi-doc matching “because Part 2 will need them”
- Collapsing shipment and document into a 1:1 model that cannot grow
- Encoding UI-upload-only assumptions into core domain types with no seam
- Treating Part 2 REQ IDs as Part 1 acceptance blockers for feature completeness
