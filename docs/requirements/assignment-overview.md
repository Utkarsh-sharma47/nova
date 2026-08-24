# Assignment overview — GoComet Nova

| Field | Value |
|-------|-------|
| Product | Nova |
| Organization context | GoComet — trade / shipping operations |
| Repository | https://github.com/Utkarsh-sharma47/nova |
| Document owner | Requirements & Product Analyst |
| Status | Phase 1 baseline |

## What Nova is

Nova is a **multi-agent operational pipeline** for trade/shipping document verification. It reads documents such as invoices and Bills of Lading, extracts key fields with confidence and evidence, checks them against **customer-specific rules**, and routes each case to **AUTO_APPROVE**, **HUMAN_REVIEW**, or **AMENDMENT_REQUEST**.

It is intended to replace expensive, inconsistent email back-and-forth between shippers and validation teams — not to act as a generic chatbot.

## Assignment parts

| Part | Intent | This repository phase |
|------|--------|-----------------------|
| **Part 1** | End-to-end single-document verification: extract → validate → route → persist → query → minimal UI, with samples, evaluation, observability, and documentation | Implement in later engineering phases; **specified now** |
| **Part 2** | Email/file triggers, multiple attachments, cross-document validation, draft replies, human approval, outbound sending | **Forward-compatibility only** — design extension points; do not implement features yet |

## Intended Part 1 pipeline (conceptual)

```text
Document
  → ingestion
  → extraction (+ confidence / evidence)
  → validation (customer rules → MATCH | MISMATCH | UNCERTAIN)
  → routing (AUTO_APPROVE | HUMAN_REVIEW | AMENDMENT_REQUEST)
  → persistence
  → query (including natural-language over persisted data)
  → minimal B2B operations UI
```

No application stages are implemented in the Phase 1 documentation delivery.

## Requirement taxonomy

Stable IDs use these categories:

| Prefix | Focus |
|--------|-------|
| `REQ-PROD` | Product / problem framing |
| `REQ-EXT` | Document input & extraction |
| `REQ-VAL` | Validation outcomes |
| `REQ-ROUTER` | Disposition routing |
| `REQ-DATA` | Persistence |
| `REQ-QUERY` | Query layer |
| `REQ-UI` | Operations UI |
| `REQ-AI` | Agent / LLM usage |
| `REQ-OBS` | Observability |
| `REQ-TEST` | Testing |
| `REQ-DEPLOY` | CI / deployment |
| `REQ-DOC` | Documentation |
| `REQ-SEC` | Security |
| `REQ-SUBMISSION` | Demo / assignment delivery |
| `REQ-PART2` | Part 2 forward compatibility |

## Source types (mandatory distinction)

| Source | Meaning |
|--------|---------|
| **ASSIGNMENT REQUIREMENT** | Stated or directly implied by the assignment brief / project context |
| **ENGINEERING REQUIREMENT** | Necessary to implement the assignment safely at production quality; does not invent product features |

Engineering requirements must not introduce capabilities outside Part 1 / Part 2 scope (for example: new document types, autonomous settlement, multi-region infra).

## Document map

| Document | Purpose |
|----------|---------|
| [functional-requirements.md](./functional-requirements.md) | Functional `REQ-*` cards |
| [non-functional-requirements.md](./non-functional-requirements.md) | Quality, ops, security, test, deploy NFRs |
| [acceptance-criteria.md](./acceptance-criteria.md) | Consolidated Part 1 acceptance checklist |
| [evaluation-rubric.md](./evaluation-rubric.md) | How delivery quality will be judged |
| [scope.md](./scope.md) | In / out of scope |
| [part-1-requirements.md](./part-1-requirements.md) | Part 1-only inventory |
| [part-2-forward-compatibility.md](./part-2-forward-compatibility.md) | Part 2 extension requirements only |
| [traceability-matrix.md](./traceability-matrix.md) | REQ → design → phase → test → evidence |

Product context lives under [`../product/`](../product/).

## Phase 1 delivery note

Phase 1 establishes the **requirements and product baseline** (this folder and `docs/product/`). Application code, agents, database, and UI are **out of scope** for this delivery.
