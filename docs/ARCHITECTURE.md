# Evidence Ledger architecture

This diagram shows the smallest complete path. The local deterministic path is the
reference contract; the AWS path exercises the same metadata boundary through an
event-driven deployment.

![Evidence Ledger architecture](architecture.svg)

```mermaid
flowchart LR
    Inputs["Synthetic input files"] --> Local["Local deterministic pipeline"]
    Local --> Package["Verified package<br/>metadata + custody events"]

    Upload["S3 incoming/ object"] --> Notify["S3 ObjectCreated notification"]
    Notify --> Processor["Lambda processor"]
    Processor --> Read["Read named object<br/>hash in memory"]
    Read --> Ledger["DynamoDB custody ledger<br/>append-only conditional write"]
    Processor --> Logs["CloudWatch Logs<br/>identifiers only"]
    Processor --> Retry{"Unexpected failure?"}
    Retry -->|No| Ledger
    Retry -->|Yes: retry twice| Processor
    Retry -->|Retries exhausted| DLQ["Encrypted SQS dead-letter queue"]

    Human["Operator"] --> Inspect["Inspect reports, logs, or DLQ"]
    Package --> Inspect
    Ledger --> Inspect
    Logs --> Inspect
    DLQ --> Inspect
```

## Trust and data boundaries

- The input boundary accepts only synthetic fixtures in this portfolio project.
- S3 stores the source object with versioning, short governance retention, public-access
  blocking, and server-side encryption.
- Lambda receives an object location and bounded metadata; it does not print or return
  source bytes.
- DynamoDB stores metadata and custody events, not a second copy of the source object.
- The failure queue stores failed invocation envelopes for inspection. It has no automatic
  replay consumer in this small, low-cost deployment.
- The optional LLM lane, if added later, may recommend metadata triage only. It cannot
  alter evidence, custody history, approval state, or verification results.

## Deliberate limits

S3 notifications are at-least-once delivery, so duplicate handling is part of the
contract. The single-region deployment does not establish regional recovery or
production-scale concurrency. A DLQ preserves a failed invocation but does not replace
alerting, ownership, replay policy, or incident response.
