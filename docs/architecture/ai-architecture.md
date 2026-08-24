# AI architecture

## Agents

| Agent | Purpose | LLM required? |
|-------|---------|---------------|
| **Extractor** | Fields + confidence + evidence | Usually yes |
| **Validator** | Rules → MATCH / MISMATCH / UNCERTAIN | Prefer no for crisp rules |
| **Router** | AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST | Prefer deterministic policy |

Specs: [`docs/agents/`](../agents/). Trust model: [ADR-0010](../decisions/0010-ai-agent-contracts-and-trust-model.md). Provider port: [ADR-0005](../decisions/0005-ai-provider-abstraction.md).

## Invariants

- Versioned Pydantic contracts (`src/nova/contracts/`)
- Propagate `trace_id`, `document_id`, `shipment_id`
- Confidence, evidence, uncertainty first-class
- Timeouts + bounded retries
- Cost/token tracking when LLM used
- **Never** map UNKNOWN/UNCERTAIN → AUTO_APPROVE without explicit versioned policy (Part 1 default: forbidden)

## Router policy sketch (defaults)

| Condition | Decision |
|-----------|----------|
| Hard MISMATCH on blocking rules | `AMENDMENT_REQUEST` or `HUMAN_REVIEW` per severity |
| UNCERTAIN / low confidence on blocking fields | `HUMAN_REVIEW` |
| Provider/timeout/retry exhausted | `HUMAN_REVIEW` — never `AUTO_APPROVE` |
| All blocking MATCH + confidence policy satisfied | `AUTO_APPROVE` |

Confidence bands: [confidence-and-evidence.md](./confidence-and-evidence.md).

## Extractor evaluation

Implemented deterministic harness (MockLLM + synthetic gold):

- Docs: [`docs/evaluation/extractor-evaluation.md`](../evaluation/extractor-evaluation.md)
- Fixtures: `fixtures/evaluation/extractor/` (`extractor-regression-v1`)
- Code: `src/nova/extraction/`, `src/nova/evaluation/extractor/`, `src/nova/llm/`
- Dogfood: `python scripts/run-extractor-eval.py` / `python scripts/dogfood-extractor.py`

Evaluation metrics are distinct from production confidence. No real-provider performance is claimed until measured.
