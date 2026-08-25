# Test strategy

Complete testing architecture for Nova. Complements [philosophy.md](./philosophy.md) and root [TESTING.md](../../TESTING.md).

**Scope of this document:** define layers, ownership, and when each suite runs.  
**Out of scope:** implementing agents, application code, or benchmark tooling.

---

## Goals

1. Protect typed contracts across Extractor → Validator → Router → persistence → query/UI.
2. Prove deterministic behavior (rules, schemas, fail-safes) in every PR CI run.
3. Measure probabilistic LLM quality with explicit evaluation harnesses — never as silent flaky CI.
4. Prefer **false AUTO_APPROVE prevention** over optimistic automation.
5. Keep Part 2 extension points testable without implementing Part 2 product features.

---

## Test pyramid

```text
                    /\
                   /  \      Evaluation / regression (gated, versioned)
                  /----\
                 / E2E  \    Representative document → decision flows
                /--------\
               / Failure  \  Timeouts, provider/DB/file faults, retries
              /------------\
             / Performance  \  Latency, throughput, cost (not PR-blocking by default)
            /----------------\
           /   Integration    \  Stage wiring + persistence + adapters
          /--------------------\
         /   Contract tests     \  Agent I/O + API schemas always green
        /------------------------\
       /        Unit tests        \  Pure logic, parsers, policy helpers
      /____________________________\
```

| Layer | Primary question | Typical speed | Default CI |
|-------|------------------|---------------|------------|
| Unit | Does this pure function behave correctly? | Fast | Always |
| Contract | Do payloads match stable schemas? | Fast | Always |
| Integration | Do stages + storage work together? | Medium | Always (when code exists) |
| Failure | Do faults fail safe (no silent AUTO_APPROVE)? | Medium | Always for critical paths |
| End-to-end | Does a real-ish document produce the right disposition? | Slow | PR smoke + fuller nightly |
| Evaluation | Is LLM quality acceptable on labeled sets? | Slow / costly | Gated / scheduled |
| Regression (eval) | Did a prompt/model change hurt fixed gold cases? | Slow | Required before release claims |
| Performance | Are latency/cost within operational budgets? | Variable | Benchmark jobs; not silent PR green |

Application suites do not exist yet. Until they do, Phase 1 CI remains docs-structure + secret-pattern checks only. Do not invent fake application tests.

---

## Layer definitions

### Unit tests

**Belong here**

- Parsers, normalizers, field transformers
- Deterministic rule helpers (equality, required presence, numeric tolerances, allow-lists)
- Router **policy helpers** that map structured validation outcomes → candidate dispositions (without calling an LLM)
- Confidence threshold checks, schema validators, idempotency key helpers
- Retry/backoff calculators, timeout budget math
- Cost/token accounting arithmetic when present

**Do not belong here**

- Live LLM calls
- Real database or network I/O
- Full pipeline “document in → decision out” flows

**Agents covered indirectly:** Extractor/Validator/Router pure post-processing and policy logic only.

### Contract tests

**Belong here**

- Extractor input/output schemas (fields, confidence, evidence, error shapes)
- Validator I/O (`MATCH` / `MISMATCH` / `UNCERTAIN`, reasons, rule IDs)
- Router I/O (`AUTO_APPROVE` / `HUMAN_REVIEW` / `AMENDMENT_REQUEST`, rationale, policy version)
- Persistence/API request–response shapes for submission, run status, query
- Compatibility between stage contracts (Validator accepts Extractor output; Router accepts Validator output)

Detail: [contract-testing.md](./contract-testing.md).

### Integration tests

**Belong here**

- Ingestion adapter → stored document reference → run ID
- Pipeline stage wiring with fakes/stubs for LLM where deterministic
- Persistence of shipment, document, extraction, validation, decision records
- Idempotent re-processing of the same document
- Query API reading persisted records
- Adapter boundaries (LLM client, object storage, DB) with test doubles or ephemeral infra

**Do not belong here**

- Measuring field accuracy vs gold labels (that is evaluation)
- Load/soak campaigns (performance)

### End-to-end tests

**Belong here**

- Representative Part 1 flows: document submit → extract → validate → route → persist → retrieve
- Golden paths for each router disposition using **fixtures with known expected outcomes**
- Minimal UI smoke (when UI exists): submit, inspect evidence, see decision
- One documented failure-path E2E (e.g. unsupported file → safe error, no AUTO_APPROVE)

Prefer synthetic/anonymized fixtures. Keep the E2E set small and stable; put breadth in unit/contract/integration and evaluation.

### Evaluation tests

**Belong here**

- Labeled document sets scored for Extractor / Validator / Router quality
- Confidence calibration and evidence correctness studies
- Safety metrics (especially false AUTO_APPROVE)
- Prompt/model comparison reports with versioned artifacts

Evaluation is **not** a substitute for unit or contract tests. See [evaluation framework](../evaluation/evaluation-framework.md).

### Regression tests

Two complementary meanings in Nova:

| Kind | What | Where |
|------|------|--------|
| **Code regression** | Previously fixed bugs stay fixed (unit/integration/failure fixtures) | Application test suite |
| **AI regression** | Fixed labeled dataset re-scored after prompt/model/policy change | Evaluation harness |

**Rule:** every future prompt, model, or routing-policy change that can alter agent behavior must be evaluated against the fixed AI regression dataset before release or quality claims. See [regression policy](../evaluation/regression-policy.md).

### Failure tests

**Belong here**

- LLM timeout, malformed output, unavailable provider, rate limiting
- Database unavailable; duplicate document; corrupt/unsupported file
- Missing fields; invalid customer rules; partial processing; retry exhaustion

Detail: [failure-testing.md](./failure-testing.md).

### Performance tests

**Belong here**

- End-to-end document processing latency
- Throughput (documents / unit time) under controlled concurrency
- LLM latency vs non-LLM stage latency vs database latency
- Cost per document (tokens + provider pricing assumptions)

Define budgets as **calibration targets** once baseline data exists. Do not invent numeric SLOs yet. Detail: [performance-testing.md](./performance-testing.md).

---

## Mapping to pipeline stages

| Stage | Unit | Contract | Integration | Failure | E2E | Evaluation |
|-------|------|----------|-------------|---------|-----|------------|
| Ingestion | File type / size helpers | Upload/run schemas | Store + run create | Corrupt/unsupported/duplicate | Submit path | — |
| Extractor | Normalizers, evidence helpers | Field + confidence + evidence schema | Stage + persistence | Timeout/malformed/unavailable | Clean/messy fixture runs | Field accuracy, missing-field, calibration, evidence |
| Validator | Deterministic rule eval | MATCH/MISMATCH/UNCERTAIN schema | Rules + extract input | Invalid rules, partial input | Rule fixture packs | Outcome accuracy per label |
| Router | Policy helpers | Decision schema | Policy + validation input | Fail-safe on upstream errors | Disposition goldens | AUTO_APPROVE precision, HUMAN_REVIEW recall, AMENDMENT correctness |
| Persistence / query / UI | Serializers | API schemas | CRUD + NL groundedness stubs | DB down | Ops smoke | NL groundedness (later) |

---

## CI placement (when application code exists)

| Suite | PR CI | Nightly / scheduled | Release gate |
|-------|-------|---------------------|--------------|
| Unit + contract | Required | Required | Required |
| Integration + critical failure | Required | Required | Required |
| E2E smoke (small) | Required when stable | Fuller set | Required |
| Evaluation / AI regression | Optional informational or manual | Required | Required for quality claims |
| Performance / cost benchmarks | No (unless budgeted job) | Required | Compare to calibrated targets |

Never mark CI green by skipping failing evaluation or by weakening assertions.

---

## Fixtures and data hygiene

- Use synthetic or anonymized documents only.
- Never commit real customer PII or production documents.
- Label gold outcomes for evaluation separately from executable unit fixtures when practical.
- Dataset categories: [datasets.md](../evaluation/datasets.md).

---

## Requirements traceability (selected)

| REQ (examples) | Primary test layers |
|----------------|---------------------|
| REQ-EXT-002–006 | Unit, contract, failure, evaluation |
| REQ-VAL-001–006 | Unit, contract, golden integration |
| REQ-ROUTER-001–005 | Unit policy, contract, failure, evaluation |
| REQ-EXT-005, REQ-SUBMISSION-002 | Evaluation + regression policy |
| REQ-TEST-* (when inventoried) | Honesty of CI and suite coverage |

---

## Implementation status

| Artifact | Status |
|----------|--------|
| This strategy | Documented |
| Application test suites | Not implemented (do not invent) |
| Evaluation harness / gold files | Not implemented |
| Benchmark tooling | Not implemented |

---

## Related documents

- [philosophy.md](./philosophy.md)
- [contract-testing.md](./contract-testing.md)
- [failure-testing.md](./failure-testing.md)
- [performance-testing.md](./performance-testing.md)
- [evaluation framework](../evaluation/evaluation-framework.md)
- [AGENTS.md](../../AGENTS.md)
- [docs/ai-development/testing-rules.md](../ai-development/testing-rules.md)
