# Delivery path

## Current controls

- GitHub Actions runs on pushes and pull requests.
- The CI job is the intended merge gate: it runs the test suite, validates the SAM template,
  and builds the Lambda package.
- The workflow has read-only repository permissions and a ten-minute timeout.
- The action references are pinned to commit hashes.
- The lockfile is committed.
- AWS deployment is not part of CI. It remains a manual, account-specific operation because
  deploying creates external resources and can spend money.

## GitHub repository check

Configured on 2026-10-22:

- The `main` branch is protected.
- The `verify` CI job is a required status check before merge.
- Branches must be up to date before merging.
- Administrator bypass is disabled.
- Force-pushes and branch deletion are disabled.
- Linear history and conversation resolution are required.
- Required approvals are intentionally not enabled because this repository currently has
  one maintainer; enabling them would block that maintainer from merging fixes.

Branch protection means GitHub blocks a merge until selected checks pass. The rule protects
the delivery path without adding a second reviewer requirement that the current ownership
model cannot satisfy.

## Not yet checkable from the repository

- Who owns the deployment approval.
- Whether an alarm destination is a distribution list.

These require repository or operational ownership decisions. A workflow file cannot prove
that GitHub enforces branch protection, and a queue without an owner is not incident
response.

## Rollback

- Code and infrastructure-template changes roll back through a Git revert.
- A deployed stack rolls back through CloudFormation update rollback or stack deletion.
- S3 object versions and governance retention are external state; they do not roll back
  through Git.
- No external message, ticket, or wiki write is performed by this repository.
