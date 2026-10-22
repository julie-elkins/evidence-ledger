# Evidence Ledger showcase

Evidence Ledger is a small, synthetic evidence pipeline built to make one claim
auditable: the system can show what it checked, what it refused, and why.

It is not a legal system. It does not decide relevance, privilege, admissibility, or
whether an export should be approved. Those limits are part of the design.

## What to notice

The project keeps the deterministic evidence contract separate from the optional model
lane:

- The local path produces reproducible metadata, totals, fingerprints, and custody events.
- Verification refuses a package when an object is missing, altered, reordered, or not
  accounted for.
- The AWS path uses S3, Lambda, and DynamoDB to exercise the same metadata boundary in an
  event-driven deployment.
- Duplicate requests are refused through an idempotency condition rather than creating a
  second custody record.
- Unexpected processing failures are retried twice. An exhausted event goes to an
  encrypted SQS dead-letter queue (DLQ), a durable holding queue for operator inspection.
- The optional LLM lane may recommend metadata triage later, but it cannot alter evidence,
  custody history, approval state, or verification results.

## Five-minute review

Start with the local path. It needs no AWS account, credentials, or model provider:

```bash
uv sync --extra dev
uv run pytest
uv run evidence-ledger demo --output /tmp/evidence-ledger-demo
uv run evidence-ledger verify --package /tmp/evidence-ledger-demo/package
```

Then read:

1. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the data and failure paths.
2. [`src/evidence_ledger/pipeline.py`](src/evidence_ledger/pipeline.py) for the
   deterministic contract.
3. [`src/evidence_ledger/ledger.py`](src/evidence_ledger/ledger.py) for the append-only
   hash chain.
4. [`src/evidence_ledger/aws_handler.py`](src/evidence_ledger/aws_handler.py) for the
   event adapter and duplicate handling.
5. [`docs/DECISIONS.md`](docs/DECISIONS.md) for the tradeoffs and limits.

## AWS review path

The AWS deployment is manual and intentionally small. It uses no always-on worker, NAT
gateway, API endpoint, or provisioned database capacity. That keeps the demonstration
affordable and makes teardown understandable, but it does not establish production scale.

The runbook covers:

- explicit account and region confirmation;
- SAM (AWS Serverless Application Model) validation and build;
- the event-driven S3 demo;
- the synthetic retry and DLQ negative control;
- exact cleanup of test objects and queue messages;
- stack inspection and teardown.

See [`docs/AWS_RUNBOOK.md`](docs/AWS_RUNBOOK.md),
[`docs/AWS_SECURITY_BASELINE.md`](docs/AWS_SECURITY_BASELINE.md), and
[`docs/AWS_WELL_ARCHITECTED.md`](docs/AWS_WELL_ARCHITECTED.md).

## Evidence of delivery discipline

The repository has:

- pinned GitHub Actions references;
- read-only CI permissions;
- a ten-minute CI timeout;
- protected `main` requiring the `verify` CI job;
- required linear history and conversation resolution;
- force-push and branch-deletion protection;
- explicit rollback notes for code, CloudFormation, S3 versions, and external queue state.

The delivery path does not pretend that a workflow file proves GitHub enforcement. The
repository records the live branch settings separately in
[`docs/DELIVERY_PATH.md`](docs/DELIVERY_PATH.md).

## What this project does not prove

- legal admissibility or regulatory compliance;
- security of an arbitrary AWS account;
- protection against a compromised administrator or operating system;
- multi-region recovery or production-scale concurrency;
- automatic incident response for failed queue messages;
- semantic correctness from an LLM (large language model);
- that a model can approve an export or change the custody record.

Those are not missing marketing claims. They are the boundary of what this implementation
actually demonstrates.
