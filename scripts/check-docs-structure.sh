#!/usr/bin/env bash
# Validate that the Phase 1 documentation system exists.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

missing=0

require() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    echo "MISSING: $path" >&2
    missing=1
  else
    echo "OK: $path"
  fi
}

echo "== Nova docs structure check =="

# Root guides
require "README.md"
require "AGENTS.md"
require "CONTRIBUTING.md"
require "DEVELOPMENT.md"
require "ARCHITECTURE.md"
require "TESTING.md"
require "SECURITY.md"
require "ROADMAP.md"
require "CHANGELOG.md"
require ".gitignore"
require ".env.example"
require ".github/workflows/ci.yml"
require ".github/PULL_REQUEST_TEMPLATE.md"

# Docs index + requirements
require "docs/README.md"
require "docs/requirements/README.md"
require "docs/requirements/inventory.md"
require "docs/requirements/acceptance-criteria.md"
require "docs/requirements/traceability.md"
require "docs/requirements/scope-boundaries.md"

# Product
require "docs/product/README.md"
require "docs/product/problem-definition.md"
require "docs/product/solution-definition.md"
require "docs/product/personas-and-users.md"

# Architecture
require "docs/architecture/README.md"
require "docs/architecture/principles.md"
require "docs/architecture/high-level-overview.md"
require "docs/architecture/part2-extension-points.md"
require "docs/architecture/engineering-standards.md"
require "docs/architecture/technology-stack.md"
require "docs/architecture/system-architecture.md"
require "docs/architecture/layering.md"
require "docs/architecture/ai-architecture.md"
require "docs/architecture/contracts.md"
require "docs/architecture/error-model.md"
require "docs/architecture/confidence-and-evidence.md"
require "docs/architecture/lifecycle-and-idempotency.md"
require "docs/architecture/contract-alignment.md"

# Features / agents / reserved
require "docs/features/README.md"
require "docs/features/part1-scope.md"
require "docs/features/FEATURE_TEMPLATE.md"
require "docs/agents/README.md"
require "docs/agents/AGENT_TEMPLATE.md"
require "docs/agents/extractor.md"
require "docs/agents/validator.md"
require "docs/agents/router.md"
require "docs/api/README.md"
require "docs/api/surface.md"
require "docs/api/endpoints.md"
require "docs/database/README.md"
require "docs/database/domain-model.md"
require "docs/database/relationships.md"
require "docs/database/indexing-strategy.md"
require "docs/database/audit-model.md"

# Quality / ops philosophies
require "docs/testing/README.md"
require "docs/testing/philosophy.md"
require "docs/testing/contract-requirements.md"
require "docs/testing/test-strategy.md"
require "docs/testing/contract-testing.md"
require "docs/testing/failure-testing.md"
require "docs/testing/performance-testing.md"
require "docs/evaluation/README.md"
require "docs/evaluation/philosophy.md"
require "docs/evaluation/architecture.md"
require "docs/evaluation/agent-evaluation.md"
require "docs/evaluation/evaluation-framework.md"
require "docs/evaluation/datasets.md"
require "docs/evaluation/metrics.md"
require "docs/evaluation/regression-policy.md"
require "docs/observability/README.md"
require "docs/observability/philosophy.md"
require "docs/observability/architecture.md"
require "docs/deployment/README.md"
require "docs/deployment/philosophy.md"
require "docs/deployment/architecture.md"
require "docs/deployment/ci-cd.md"
require "docs/security/README.md"
require "docs/security/baseline.md"
require "docs/security/architecture.md"
require "docs/operations/README.md"
require "docs/operations/git-workflow.md"

# Decisions / AI / audits / roadmap
require "docs/decisions/README.md"
require "docs/decisions/ADR_TEMPLATE.md"
require "docs/decisions/0001-documentation-first-phase1.md"
require "docs/decisions/0002-backend-stack.md"
require "docs/decisions/0003-database.md"
require "docs/decisions/0004-api-framework.md"
require "docs/decisions/0005-ai-provider-abstraction.md"
require "docs/decisions/0006-document-processing.md"
require "docs/decisions/0007-observability.md"
require "docs/decisions/0008-deployment.md"
require "docs/decisions/0009-frontend-stack.md"
require "docs/ai-development/README.md"
require "docs/ai-development/governance.md"
require "docs/ai-development/agent-development-rules.md"
require "docs/ai-development/git-rules.md"
require "docs/audits/README.md"
require "docs/audits/AUDIT_TEMPLATE.md"
require "docs/audits/phase-2-architecture-audit.md"
require "docs/audits/phase-2-audit.md"
require "docs/roadmap/README.md"
require "docs/roadmap/roadmap.md"

# Phase 2 contracts skeleton
require "pyproject.toml"
require "src/nova/contracts/__init__.py"
require "tests/contracts/test_schemas.py"
require "Dockerfile"
require "docker-compose.yml"

require "docs/decisions/0010-ai-agent-contracts-and-trust-model.md"

require "docs/database/schema-design.md"

require "docs/agents/contracts.md"

require "docs/agents/trust-model.md"

require "docs/api/contracts.md"

require "docs/api/error-model.md"

require "docs/api/idempotency.md"

require "docs/api/versioning.md"

require "docs/api/query-interface.md"

require "docs/audits/phase-10-audit.md"
require "docs/testing/phase-10-system-verification.md"

# Scripts
require "scripts/check-docs-structure.sh"
require "scripts/check-secret-patterns.sh"
require "scripts/run_full_evaluation.py"

for cat in REQ-PROD REQ-EXT REQ-VAL REQ-ROUTER REQ-DATA REQ-QUERY REQ-UI REQ-AI REQ-OBS REQ-TEST REQ-DEPLOY REQ-DOC REQ-SEC REQ-SUBMISSION REQ-PART2; do
  if ! grep -q "$cat" docs/requirements/inventory.md; then
    echo "MISSING CATEGORY IN INVENTORY: $cat" >&2
    missing=1
  else
    echo "OK: inventory contains $cat"
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo "Docs structure check FAILED" >&2
  exit 1
fi

echo "Docs structure check PASSED"
