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

# Features / agents / reserved
require "docs/features/README.md"
require "docs/features/part1-scope.md"
require "docs/features/FEATURE_TEMPLATE.md"
require "docs/agents/README.md"
require "docs/agents/AGENT_TEMPLATE.md"
require "docs/api/README.md"
require "docs/database/README.md"

# Quality / ops philosophies
require "docs/testing/README.md"
require "docs/testing/philosophy.md"
require "docs/evaluation/README.md"
require "docs/evaluation/philosophy.md"
require "docs/observability/README.md"
require "docs/observability/philosophy.md"
require "docs/deployment/README.md"
require "docs/deployment/philosophy.md"
require "docs/deployment/ci-cd.md"
require "docs/security/README.md"
require "docs/security/baseline.md"
require "docs/operations/README.md"
require "docs/operations/git-workflow.md"

# Decisions / AI / audits / roadmap
require "docs/decisions/README.md"
require "docs/decisions/ADR_TEMPLATE.md"
require "docs/decisions/0001-documentation-first-phase1.md"
require "docs/ai-development/README.md"
require "docs/ai-development/governance.md"
require "docs/ai-development/agent-development-rules.md"
require "docs/ai-development/git-rules.md"
require "docs/audits/README.md"
require "docs/audits/AUDIT_TEMPLATE.md"
require "docs/roadmap/README.md"
require "docs/roadmap/roadmap.md"

# Scripts
require "scripts/check-docs-structure.sh"
require "scripts/check-secret-patterns.sh"

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
