# AWS Well-Architected design record

The AWS Well-Architected Framework has six pillars: operational excellence, security,
reliability, performance efficiency, cost optimization, and sustainability. Evidence
Ledger treats the framework as a set of design questions, not a claim that this small
portfolio deployment is production-ready.

## Operational excellence

- Deployment is defined in `infra/template.yaml`, not in a personal shell configuration.
- The deployment prints the account, region, stack name, and expected resources before it
  creates anything.
- Logs contain identifiers, statuses, counts, hashes, and reasons only.
- Lambda retry exhaustion is observable in CloudWatch logs and the encrypted failure
  queue; the runbook gives an operator a bounded inspection and cleanup path.
- The demo has a bounded input fixture and a documented teardown path.
- A deployment report records the Git revision and template fingerprint.

Not demonstrated: team paging, multi-person on-call operation, or production change
management.

## Security

- S3 public access is blocked.
- S3 transport is required to use TLS.
- S3 objects use server-side encryption with S3-managed keys.
- S3 versioning and a short governance retention window protect the synthetic source
  package from accidental overwrite or deletion.
- Lambda has a dedicated execution role with only the S3 read, DynamoDB write/query, and
  CloudWatch Logs permissions needed by the demo.
- The custody table has no application update or delete permission.
- The Lambda role can send to the named failure queue but cannot consume or delete its
  messages.
- No long-lived credentials are stored in the repository or deployment package.

Not demonstrated: a production identity provider, organisation-level SCPs, a custom KMS
key, CloudTrail data events, or a formal security review sign-off.

## Reliability

- Local execution is the reference path and can rebuild a package from synthetic inputs.
- Every candidate input has an explicit outcome.
- The custody ledger is append-only and hash-chained.
- Package verification detects missing, extra, reordered, or modified objects and events.
- Duplicate event writes are rejected by an idempotency condition.
- Unexpected processing failures are retried twice and then delivered to an SQS
  dead-letter queue (DLQ), preserving the failed invocation for inspection.
- Deterministic refusals are returned without retry, so malformed or duplicate requests
  do not create an unbounded retry loop.
- The demo processes one matter sequentially; concurrent event ordering is explicitly not
  established by this project.

Not demonstrated: multi-region recovery, high availability, or a tested regional failover.

## Performance efficiency

The workload is intentionally small and bounded. The project will measure object count,
package size, Lambda duration, and DynamoDB write count during the AWS demo, but it will
not claim large-scale performance from a portfolio fixture.

## Cost optimization

- No NAT gateway, RDS cluster, OpenSearch domain, queue consumer, or always-on API.
- Lambda is invoked by an S3 `ObjectCreated` notification filtered to the `incoming/`
  prefix; the demo performs one direct replay only to verify idempotency.
- DynamoDB uses on-demand capacity.
- SQS uses one managed-encryption queue with a 14-day retention window and no always-on
  consumer, keeping the failure path inspectable without adding worker cost.
- CloudWatch log retention is short.
- Teardown deletes the disposable stack and checks for remaining resources.

The cost ceiling is a modelling assumption, not an AWS billing guarantee. The deployment
must be run only in an account where the operator can inspect and stop spend. The queue
is intentionally retained with the stack; a growing failure queue would be an operational
signal and a cost to manage, not a silent success state.

## Sustainability

The design avoids idle compute and avoids provisioning for a scale the project does not
need. This is a small demonstration, so no energy or carbon measurement is established.

## Review status

This is a design record for the portfolio deployment. It is not a Well-Architected Tool
review and does not represent AWS or Anthropic approval.

## Primary reference

- [AWS Well-Architected Framework definitions and six pillars](https://docs.aws.amazon.com/wellarchitected/latest/framework/definitions.html)
