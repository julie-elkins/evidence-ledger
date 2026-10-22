# Security triage

## Data class

Neither. The repository contains synthetic records only and must not contain real
personal data, legal matter data, credentials, or private source material.

## Review verdict

Required before AWS deployment because the project creates cloud resources and stores
objects and audit records. The review is complete for this portfolio scope; this is not a
production security approval.

## Cost

The deployment uses on-demand storage, compute, database, queue, and short-retention logs.
It avoids NAT gateways, databases with provisioned capacity, always-on workers, and an API
endpoint. The retained stack and deployment bucket still create external state and must
be inspected or deleted when no longer needed.

## Status

Completed for the current portfolio scope on 2026-10-22. Evidence includes 14 passing
tests, SAM template lint and build, IAM policy analysis with no findings, a successful
event-driven AWS smoke test, and a synthetic negative control (an intentional failure
used to prove the refusal/retry path) that reached the encrypted failure queue after
three attempts.

## Controls verified

- Account and region are printed and confirmed before deployment.
- S3 public access is blocked and transport is required to be encrypted.
- S3 objects use server-side encryption and versioning.
- The custody ledger has no application update or delete operation.
- Lambda permissions are limited to the named bucket, table, logs, and failure queue.
- Logs contain identifiers, statuses, counts, and hashes only.
- A negative-control deployment proves retry exhaustion and failure-queue delivery.
- Teardown and synthetic test cleanup use exact resource identifiers.

## Remaining limits

This review does not establish account-wide security, organisation guardrails, central
logging, CloudTrail data events, incident response, multi-account separation, a
customer-managed encryption key, GitHub branch protection, or production approval.
