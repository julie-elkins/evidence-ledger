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

Checked against the public repository on 2026-10-22:

- The `main` branch is not protected.
- The CI workflow exists, but GitHub does not currently enforce it as a required status
  check before merge.
- No deployment approval owner is recorded in repository configuration.

Branch protection means GitHub blocks a merge until selected checks pass. It is a shared
repository setting, so this project documents the gap but does not change it from code.
The recommended manual hardening is to protect `main`, require the CI job named `verify`,
require branches to be up to date before merging, and require approval from a second
reviewer when the repository has another maintainer.

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
