# Evidence Ledger decisions

## Local execution

**Decided:** Build the deterministic local path before the AWS adapter.

**Instead of:** Starting with a cloud-first event pipeline.

**Why:** A reviewer can reproduce the evidence contract without credentials or spend, and
the AWS adapter can then be checked against a known local result.

**Costs if wrong:** The two paths could diverge and the project could prove only that the
cloud wiring works, not that the data contract is correct.

**Decided by:** Julie Elkins, 2026-10-22.

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
