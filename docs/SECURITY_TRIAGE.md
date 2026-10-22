# Security triage

## Data class

Neither. The repository contains synthetic records only and must not contain real
personal data, legal matter data, credentials, or private source material.

## Review verdict

Required before any AWS deployment because the project creates cloud resources and stores
objects and audit records. This is a portfolio deployment, not a production service.

## Cost

Plan for a short review window before the first cloud deployment. Remediation cost is not
established until the review identifies findings. The AWS path must remain disposable and
must not create always-on resources.

## Status

Not started. No AWS resources are created by the local path.

## Controls required before AWS deployment

- Account and region are printed and confirmed before deployment.
- S3 public access is blocked and transport is required to be encrypted.
- S3 objects use server-side encryption and versioning.
- The custody ledger has no application update or delete operation.
- Lambda permissions are limited to the named bucket and table.
- Logs contain identifiers, statuses, counts, and hashes only.
- A negative-control deployment proves the refusal path runs.
- Teardown checks the resource inventory after deletion.
