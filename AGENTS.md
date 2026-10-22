# Evidence Ledger repository instructions

## Data boundary

This repository handles synthetic evidence fixtures only. It must never contain real
personal data, legal matter data, customer records, credentials, private URLs, or copied
source material. A report may contain identifiers, paths, hashes, statuses, counts, and
reasons. It must not contain source bytes or excerpts.

Raw fixture bytes may exist only under an explicitly named local run package or an AWS S3
object in the synthetic deployment. They must not appear in logs, errors, tracebacks,
tests, reports, commit messages, or documentation.

## Project rules

- Deterministic means identical inputs and an explicit `as_of` timestamp produce identical
  metadata, hashes, and event ordering.
- Every candidate input receives exactly one outcome: `INGESTED`, `SKIPPED`, or `FAILED`.
- Every report publishes `input_count`, `ingested_count`, `skipped_count`, `failed_count`,
  `output_count`, and `unprocessed_count`; the totals must reconcile.
- A refusal is a structured result with `code`, `message`, and `guidance`.
- Custody events are append-only. No update or delete operation may rewrite their history.
- A clean result is not reported when verification was not completed.
- AWS deployment must be disposable, region-explicit, and free of always-on resources.
- The optional LLM lane may recommend metadata triage only. It cannot alter evidence,
  approve an export, or convert missing evidence into success.

## Verification

Run the local suite before calling a change complete:

```bash
uv run pytest
uv run evidence-ledger demo --output /tmp/evidence-ledger-demo
uv run evidence-ledger verify --package /tmp/evidence-ledger-demo/package
```

The demo output is disposable and must not be committed.
