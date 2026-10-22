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
and one short-retention CloudWatch log group. It does not create a NAT gateway, RDS
cluster, OpenSearch domain, API Gateway, or continuously running worker.

## Run the synthetic demo

```bash
uv run --extra aws python tools/aws_demo.py --stack-name <stack-name> --region <region>
```

The script uploads only `examples/good-matter/input`, waits for S3 notifications to invoke
Lambda, replays each resulting request once to verify duplicate refusal, and prints
identifiers, statuses, counts, and hashes. It does not print source bytes.

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
least-privilege Lambda access, an append-only custody record, and disposable deployment.

It does not prove account-wide security, high availability, concurrent event ordering,
legal relevance, courtroom admissibility, or production scale.
