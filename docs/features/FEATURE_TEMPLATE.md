# Feature documentation template

Copy this file for each significant feature. Fill every section that applies. Mark undecided items as **TBD** rather than inventing details.

---

# Feature: \<Name\>

| Field | Value |
|-------|-------|
| Status | Proposed / In progress / Shipped / Deprecated |
| Owner | |
| Last updated | YYYY-MM-DD |
| Related requirements | |
| Related ADR(s) | |
| Related agent(s) | |

## 1. Purpose

Why this feature exists and the user/business outcome it enables.

## 2. Requirements

Functional and non-functional requirements (link to `docs/requirements/` where possible).

## 3. User workflow

Step-by-step flow for the primary user(s).

## 4. Architecture

Components involved and how they fit the system. Link ADRs; do not invent stack choices.

## 5. Data flow

Inputs → transformations → outputs. Note persistence and retention if known.

## 6. Interfaces / API

External or internal interfaces this feature exposes or consumes.

## 7. Dependencies

Upstream/downstream features, agents, services, and data sources.

## 8. Failure modes

| Failure | Impact | Handling |
|---------|--------|----------|
| | | |

## 9. Security

AuthZ, sensitive data, abuse cases, and controls.

## 10. Testing

Test plan and key cases (unit, integration, e2e).

## 11. Evaluation

Quality metrics, gold sets, and acceptance thresholds if applicable.

## 12. Observability

Logs, metrics, traces, and alerts needed to operate the feature.

## 13. Deployment

Flags, migrations, rollout, and rollback notes.

## 14. Known limitations

## 15. Future extension

Planned extensions that are explicitly out of scope now.
