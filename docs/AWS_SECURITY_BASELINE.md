# AWS security baseline

This baseline translates AWS security guidance into controls that can be checked in the
Evidence Ledger template and deployment evidence.

The control choices are grounded in AWS guidance for IAM temporary credentials and
least-privilege permissions, Lambda execution-role isolation, and S3 public-access
blocking, versioning, and Object Lock. The links are included so a reviewer can inspect
the source rather than treating this document as authority.

## Identity and access

The deployment uses temporary credentials supplied by the operator's AWS CLI session. It
does not create IAM users or store access keys. The Lambda function has its own role, and
the role is scoped to the named Evidence Ledger bucket, custody table, and log group.

The deployer and the Lambda execution role are separate identities. The Lambda role cannot
create IAM resources, deploy code, delete evidence, or update custody events.

## Storage

The evidence bucket:

- blocks all public access;
- requires TLS for bucket actions;
- enables versioning;
- enables short governance retention for the synthetic demo;
- uses S3-managed server-side encryption;
- separates incoming objects from derived metadata.

The custody table:

- uses server-side encryption;
- uses on-demand capacity;
- allows the function to write and query events;
- does not grant the function update or delete permissions.

S3 Object Lock is a storage control, not proof that the evidence is legally admissible.
The demo uses a short retention period so teardown remains possible with the documented
governance bypass procedure.

## Lambda

The function:

- receives only an object location and bounded metadata;
- reads the named incoming object;
- computes its fingerprint in memory;
- writes metadata and the custody event;
- logs identifiers and measurements, never source bytes;
- rejects replayed event identifiers.

The function package contains no credentials or secrets.

## Verification

The AWS phase must include these checks:

1. Anonymous access to the bucket is denied.
2. A non-TLS bucket request is denied.
3. The Lambda role cannot delete a source object.
4. The Lambda role cannot update or delete a custody event.
5. Replaying the same event does not create a second ledger record.
6. Modifying an object makes package verification fail.
7. Teardown leaves no stack-owned bucket, table, function, or log group.

## Explicit limits

This baseline does not establish account-wide security. It does not cover organisation
guardrails, central logging, CloudTrail data events, incident response, multi-account
separation, a custom KMS key, or a formal security review.

## Primary references

- [AWS IAM security best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS Lambda security overview](https://docs.aws.amazon.com/pdfs/whitepapers/latest/security-overview-aws-lambda/security-overview-aws-lambda.pdf)
- [Amazon S3 security best practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [Amazon S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)
