# nova

A multi-agent AI pipeline that reads trade shipping documents (Bill of Lading, Invoice, etc.), pulls out key fields, checks them against a customer's rules, and decides whether to auto-approve, flag for human review, or request corrections — replacing the manual email back-and-forth between the shipper and the validation team.

## Phase 1 status

Repository Git workflow and CI foundation. Application packages are not implemented yet.

| Doc | Purpose |
|-----|---------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | Branch model, conventional commits, PR rules |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Local checks and day-to-day workflow |
| [SECURITY.md](SECURITY.md) | Secrets handling and vulnerability reporting |
| [docs/deployment/ci-cd.md](docs/deployment/ci-cd.md) | CI jobs and how to extend them |

## Local Phase 1 checks

```bash
./scripts/check-docs-structure.sh
./scripts/check-secret-patterns.sh
```
