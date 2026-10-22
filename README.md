# Evidence Ledger

Evidence Ledger is a synthetic, auditable evidence pipeline for controlled legal and
privacy workflows. It demonstrates how a system can preserve source artifacts, record
chain of custody, verify integrity, and refuse to report a clean result when evidence is
missing or altered.

“Chain of custody” means a tamper-evident record of which artifact was handled, when, and
under which authorization. This project is a portfolio reference implementation, not a
legal system, compliance certification, or claim of courtroom admissibility.

## Current status

The local deterministic path is the reference slice. The AWS adapter is deployed as a
disposable, on-demand event-driven path: an S3 object-created notification invokes Lambda,
which writes metadata and an append-only custody event to DynamoDB. Lambda retries
unexpected processing failures twice and sends exhausted events to an encrypted SQS
dead-letter queue (DLQ), a durable holding queue for failures that need inspection.

## Run the local path

The project uses Python 3.13 and `uv`.

```bash
uv sync --extra dev
uv run pytest
uv run evidence-ledger demo --output /tmp/evidence-ledger-demo
uv run evidence-ledger verify --package /tmp/evidence-ledger-demo/package
```

The demo prints metadata only. Source bytes remain inside the local package directory and
are never printed by the CLI.

## What the local path proves

- Every candidate input receives an explicit outcome.
- The published totals reconcile to the candidate inputs.
- Custody events form a verifiable hash chain.
- The package can be independently verified.
- A modified object is refused rather than reported as clean.
- Identical inputs with the same `as_of` timestamp produce identical metadata.

## What it does not prove

- Legal relevance, privilege, admissibility, or regulatory compliance.
- Security of an arbitrary AWS account.
- Protection against a compromised operating system or administrator.
- Semantic correctness of a future model-generated classification.

## Design guides

The implementation follows the repository's evidence-contract, refusal-as-result,
metadata-only-boundary, deliberately-degraded-negative-control, human-approval-boundary,
and self-service-path patterns. The state model also follows the house rule that failed
work becomes a record and that totals carry their denominator.

AWS-specific decisions are recorded in
[`docs/AWS_WELL_ARCHITECTED.md`](docs/AWS_WELL_ARCHITECTED.md) and
[`docs/AWS_SECURITY_BASELINE.md`](docs/AWS_SECURITY_BASELINE.md).

The deployment runbook includes the synthetic failure probe used to verify retries and
DLQ delivery. The probe is disabled by default and is never intended for real evidence.

## Portfolio walkthrough

The shortest useful review path is:

1. Run the deterministic local demo and verify its package.
2. Read the architecture diagram to see the local contract and AWS event path.
3. Run the bounded AWS demo against an explicitly selected account and region.
4. Inspect the duplicate-event refusal and, if needed, run the synthetic retry/DLQ check.
5. Review the security baseline, delivery path, and decision record for the tradeoffs.

```bash
uv sync --extra dev --extra aws
uv run pytest
uv run evidence-ledger demo --output /tmp/evidence-ledger-demo
uv run evidence-ledger verify --package /tmp/evidence-ledger-demo/package
sam validate --template-file infra/template.yaml --lint
sam build --template-file infra/template.yaml
AWS_PROFILE=<profile> AWS_REGION=<region> AWS_DEFAULT_REGION=<region> uv run --extra aws python tools/aws_demo.py --stack-name <stack-name> --region <region>
```

The local path proves deterministic metadata, reconciliation, hash-chain verification,
and refusal of altered inputs. The AWS path proves encrypted storage, event-driven
processing, append-only custody records, duplicate protection, and retry exhaustion
handling. AWS deployment remains manual because it creates external resources and can
spend money.

The project intentionally does not claim legal admissibility, production availability,
account-wide security, multi-region recovery, semantic correctness from a model, or
automatic incident response.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md),
[`docs/AWS_RUNBOOK.md`](docs/AWS_RUNBOOK.md), and
[`docs/DELIVERY_PATH.md`](docs/DELIVERY_PATH.md) for the review evidence.
