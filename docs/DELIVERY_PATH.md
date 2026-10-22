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

## Not yet checkable locally

- Whether the GitHub default branch is protected.
- Whether the CI workflow is configured as a required status check.
- Who owns the deployment approval.
- Whether an alarm destination is a distribution list.

These must be checked after the repository exists on GitHub. A local workflow file cannot
prove that GitHub enforces it.

## Rollback

- Code and infrastructure-template changes roll back through a Git revert.
- A deployed stack rolls back through CloudFormation update rollback or stack deletion.
- S3 object versions and governance retention are external state; they do not roll back
  through Git.
- No external message, ticket, or wiki write is performed by this repository.
