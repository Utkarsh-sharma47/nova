# Evaluation rubric

How Nova Part 1 delivery quality will be judged. Rubric rows map to requirement IDs so an auditor can score and evidence together.

## Scoring scale

| Score | Meaning |
|-------|---------|
| 0 | Missing or contradicts assignment |
| 1 | Partial / incomplete evidence |
| 2 | Meets acceptance criteria with reproducible evidence |
| 3 | Exceeds with clear production-quality engineering (without inventing scope) |

Maximum score is the sum of category maxima below. Categories are weighted toward **correct operational behavior** and **safe routing**, not UI polish.

---

## 1. Problem & product fidelity (weight 10)

| Criterion | REQ IDs | Max | Notes |
|-----------|---------|-----|-------|
| Operational verification framing (not chatbot demo) | REQ-PROD-001, REQ-PROD-002 | 3 | Docs + demo narrative |
| Human-in-the-loop / no blind auto-approve | REQ-PROD-003, REQ-PROD-004 | 3 | Policy + demos |
| Clear Part 1 vs Part 2 separation | scope, REQ-PART2-* | 4 | Docs + architecture extension points |

**Category max: 10**

---

## 2. Extraction quality (weight 20)

| Criterion | REQ IDs | Max | Notes |
|-----------|---------|-----|-------|
| Required fields extracted on clean sample | REQ-EXT-002 | 6 | Golden/eval |
| Confidence present and used downstream | REQ-EXT-003 | 4 | Schema + routing impact |
| Evidence/grounding usable in review | REQ-EXT-004 | 5 | Sample payloads / UI |
| Messy sample handled without silent certainty | REQ-EXT-005, REQ-AI-004 | 5 | Eval report |

**Category max: 20**

---

## 3. Validation & routing correctness (weight 25)

| Criterion | REQ IDs | Max | Notes |
|-----------|---------|-----|-------|
| Customer-specific rules applied | REQ-VAL-001 | 5 | Fixture rule pack |
| MATCH / MISMATCH / UNCERTAIN all demonstrated | REQ-VAL-002–004 | 6 | Golden suite |
| AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST all demonstrated | REQ-ROUTER-001–003 | 6 | Golden suite |
| Fail-safe on errors (no silent AUTO_APPROVE) | REQ-ROUTER-005, REQ-EXT-006 | 5 | Failure tests |
| Explicit policy / deterministic-where-possible | REQ-ROUTER-004, REQ-VAL-005 | 3 | Design + tests |

**Category max: 25**

---

## 4. Persistence, query, UI (weight 15)

| Criterion | REQ IDs | Max | Notes |
|-----------|---------|-----|-------|
| Core records persisted | REQ-DATA-001 | 5 | Integration |
| Query layer + grounded NL query | REQ-QUERY-001–003 | 5 | Eval cases |
| Minimal ops UI with evidence visibility | REQ-UI-001–002 | 5 | Demo checklist |

**Category max: 15**

---

## 5. Observability, evaluation, submission (weight 15)

| Criterion | REQ IDs | Max | Notes |
|-----------|---------|-----|-------|
| Structured logs + run correlation | REQ-OBS-001–002, REQ-OBS-004 | 5 | Samples |
| Reproducible eval on clean + messy | REQ-EXT-005, REQ-SUBMISSION-002 | 5 | Eval artifacts |
| End-to-end demo including failure path | REQ-SUBMISSION-001, REQ-SUBMISSION-003 | 5 | Demo notes |

**Category max: 15**

---

## 6. Engineering quality & hygiene (weight 15)

| Criterion | REQ IDs | Max | Notes |
|-----------|---------|-----|-------|
| Real tests / contracts / no fake green | REQ-TEST-001–004 | 5 | CI |
| CI honest and applicable | REQ-DEPLOY-001–002 | 3 | Workflows |
| Secrets hygiene | REQ-SEC-001–002 | 3 | Scans |
| Documentation & agent contracts | REQ-DOC-001, REQ-AI-001–003 | 4 | Docs tree |

**Category max: 15**

---

## Totals

| Category | Max |
|----------|-----|
| Problem & product fidelity | 10 |
| Extraction quality | 20 |
| Validation & routing correctness | 25 |
| Persistence, query, UI | 15 |
| Observability, evaluation, submission | 15 |
| Engineering quality & hygiene | 15 |
| **Total** | **100** |

## Pass guidance

| Result | Guideline |
|--------|-----------|
| Pass | ≥ 70 **and** no zero on any P0 assignment criterion in categories 2–3 |
| Conditional | 55–69 with clear remediation plan tied to REQ IDs |
| Fail | < 55 **or** any silent auto-approve on failure/uncertainty |

## Part 2 scoring note

Part 2 features are **not scored as implemented functionality** in Part 1. Credit is given only for **documented extension points** (REQ-PART2-*) under category 1. Implementing Part 2 early does not replace missing Part 1 evidence.
