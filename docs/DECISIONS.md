# Evidence Ledger decisions

## Local execution

**Decided:** Build the deterministic local path before the AWS adapter.

**Instead of:** Starting with a cloud-first event pipeline.

**Why:** A reviewer can reproduce the evidence contract without credentials or spend, and
the AWS adapter can then be checked against a known local result.

**Costs if wrong:** The two paths could diverge and the project could prove only that the
cloud wiring works, not that the data contract is correct.

**Decided by:** Julie Elkins, 2026-10-22.

## Deployment identity

**Decided:** Use a scoped CloudFormation service role for the retained AWS stack.

**Instead of:** Recreating a long-lived IAM access key or using an account-admin
identity as the routine deployment principal.

**Why:** The account currently exposes a root-backed console login but no usable
non-root principal that can assume a deployment role. A CloudFormation service role
keeps resource-creation permissions in a reviewable policy while the bootstrap login
remains temporary.

**Costs if wrong:** The bootstrap command still runs under a root-backed session until
IAM Identity Center or another non-root principal is configured. The service policy
is region-limited and project-scoped for resource families, but CloudFormation control
actions are not yet restricted to one stack ARN.

**Decided by:** Julie Elkins and Codex, 2026-10-22.

## Cloud resources

**Decided:** Use disposable, on-demand AWS resources and avoid always-on services.

**Instead of:** Building around RDS, OpenSearch, NAT gateways, or a continuously running API.

**Why:** The project needs to demonstrate AWS storage, processing, identity, encryption,
and auditability while keeping spend small and teardown straightforward.

**Costs if wrong:** The deployment may be less representative of a large production estate,
and the design will need to state which scale properties are not demonstrated.

**Decided by:** Julie Elkins, 2026-10-22.

## Source reporting

**Decided:** Reports contain identifiers, paths, hashes, statuses, counts, and reasons,
but never source bytes or excerpts.

**Instead of:** Printing evidence content in a reviewer-facing report.

**Why:** A report should prove what the system checked without becoming a second copy of the
material being checked.

**Costs if wrong:** A reviewer may need to inspect the local package separately to understand
the synthetic fixture, and a future content-bearing feature would need a new authorization
decision.

**Decided by:** Julie Elkins, 2026-10-22.
