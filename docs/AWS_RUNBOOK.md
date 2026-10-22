# AWS runbook

This runbook is for the disposable synthetic deployment. It does not deploy automatically
and it never uses real matter data.

## Preconditions

- AWS CLI and AWS SAM CLI are installed.
- The active AWS identity is the account where the disposable stack may be created.
- The selected region is explicit.
- The account has a small spend ceiling monitored by the operator.
- No unattended loop is running. The stop condition is one synthetic fixture, one stack,
  one sequential processor invocation per input file, and teardown immediately after
  verification.

## Validate and build

```bash
sam validate --template-file infra/template.yaml --lint
sam build --template-file infra/template.yaml
```

## Confirm identity and deploy

Replace the placeholders before running. The confirmation step exists because an AWS
account and region are external state, not a local test fixture.

```bash
aws sts get-caller-identity
sam deploy --template-file .aws-sam/build/template.yaml --stack-name <stack-name> --s3-bucket <deployment-bucket> --role-arn <cloudformation-service-role-arn> --capabilities CAPABILITY_IAM --region <region>
```

For the retained portfolio stack, the current values are:

```bash
AWS_PROFILE=evidence-ledger-console AWS_REGION=us-east-2 AWS_DEFAULT_REGION=us-east-2 aws sts get-caller-identity --region us-east-2
AWS_PROFILE=evidence-ledger-console AWS_REGION=us-east-2 AWS_DEFAULT_REGION=us-east-2 sam deploy --template-file .aws-sam/build/template.yaml --stack-name el-20261022 --s3-bucket evidence-ledger-deploy-262250696140-us-east-2 --role-arn arn:aws:iam::262250696140:role/EvidenceLedgerDeploymentRole --capabilities CAPABILITY_IAM --parameter-overrides RetentionDays=1 --no-confirm-changeset --no-fail-on-empty-changeset --region us-east-2
```

`EvidenceLedgerDeploymentRole` is a CloudFormation service role, meaning CloudFormation
uses its scoped policy to create or update the stack resources. Its trust policy and
permissions are stored in `infra/deployment-role-trust-policy.json` and
`infra/deployment-role-policy.json`. The current console-backed profile is a bootstrap
path only; replace the root session with an IAM Identity Center or other non-root
principal before treating this as a routine deployment workflow.

The stack creates one S3 bucket, one DynamoDB table, one Lambda function, one IAM role,
one encrypted SQS failure queue, and one short-retention CloudWatch log group. Lambda
retries unexpected processing failures twice before sending the failed invocation to the
failure queue. It does not create a NAT gateway, RDS cluster, OpenSearch domain, API
Gateway, or continuously running worker.

## Run the synthetic demo

```bash
uv run --extra aws python tools/aws_demo.py --stack-name <stack-name> --region <region>
```

The script uploads only `examples/good-matter/input`, waits for S3 notifications to invoke
Lambda, replays each resulting request once to verify duplicate refusal, and prints
identifiers, statuses, counts, and hashes. It does not print source bytes.

## Verify retries and dead-letter delivery

A dead-letter queue (DLQ) is a durable queue for an event that still fails after the
configured retry attempts. The template includes a disabled-by-default synthetic failure
probe so the operational path can be demonstrated without introducing a real failure.
Run this only with the repository's synthetic fixture and remove the probe immediately
after verification.

Set `FailureProbeKey` to the exact `incoming/` key that will be uploaded, deploy, and
upload the fixture. The expected result is three Lambda attempts: the original attempt
plus two retries, followed by one SQS message whose invocation record says
`condition: "RetriesExhausted"` and `approximateInvokeCount: 3`.

```bash
sam deploy --template-file .aws-sam/build/template.yaml --stack-name <stack-name> --s3-bucket <deployment-bucket> --role-arn <cloudformation-service-role-arn> --capabilities CAPABILITY_IAM --parameter-overrides RetentionDays=1 FailureProbeKey=incoming/failure-probe/<run-id>/controlled.txt --no-confirm-changeset --no-fail-on-empty-changeset --region <region>
aws s3 cp examples/good-matter/input/custodian-alice.txt s3://<evidence-bucket>/incoming/failure-probe/<run-id>/controlled.txt --sse AES256
aws logs tail /aws/lambda/<function-name> --since 10m --format short --region <region>
aws sqs receive-message --queue-url <failure-queue-url> --max-number-of-messages 1 --wait-time-seconds 20 --region <region>
```

After the check, delete only the synthetic probe object version, delete the received
synthetic queue message, and redeploy with `FailureProbeKey` set to an empty value. Do
not bypass Object Lock governance retention for any object that was not created by this
run. The normal AWS demo does not enable the probe.

## Inspect and tear down

Before teardown, inspect the stack outputs and the object-lock retention state. Governance
retention is intentionally short, but the operator must not bypass retention on a resource
they did not create.

```bash
aws cloudformation describe-stacks --stack-name <stack-name> --region <region>
aws s3api list-object-versions --bucket <bucket-name> --region <region>
aws cloudformation delete-stack --stack-name <stack-name> --region <region>
aws cloudformation wait stack-delete-complete --stack-name <stack-name> --region <region>
```

After deletion, confirm that the stack-owned bucket, table, function, and log group are
gone. If object-lock retention prevents deletion, wait for the documented short window
instead of broadening permissions or deleting an unrelated resource.

## What this run proves

It demonstrates a bounded AWS data path with identity separation, encrypted storage,
least-privilege Lambda access, append-only custody records, retry and dead-letter
handling, and disposable deployment.

It does not prove account-wide security, high availability, concurrent event ordering,
legal relevance, courtroom admissibility, or production scale.
