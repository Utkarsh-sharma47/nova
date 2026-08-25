# Deployment philosophy

## Part 1 stance

Prefer the **simplest** deployment that can run the demo reliably:

- One application environment
- One managed or local database
- Explicit environment configuration via `.env` / secrets store
- No requirement for multi-region active-active

## Progressive complexity

Only add queues, workers, and extra services when a concrete Part 1/Part 2 requirement demands them (e.g., email ingestion volume).

## Configuration

- All secrets outside git
- Documented `.env.example`
- Feature flags only if needed for safe rollout of LLM changes

## Rollback

- Keep demos reproducible via tagged releases or documented commit SHAs
- Record model versions so “rollback” includes prompt/model pin, not only app code
