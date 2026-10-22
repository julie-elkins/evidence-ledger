"""AWS Lambda adapter for one bounded custody-ingest operation.

1. The function reads one named synthetic object and writes metadata only.
2. The execution role is intentionally unable to delete or update custody history.
3. The event id is the idempotency key; a replay cannot create a second event.
4. Source bytes are hashed in memory and never written to logs or DynamoDB.
"""

from __future__ import annotations

import os
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from .canonical import sha256_bytes, sha256_json
from .ledger import make_event

def _refusal(code: str, message: str, guidance: str) -> dict[str, Any]:
    return {
        "status": "REFUSED",
        "code": code,
        "message": message,
        "guidance": guidance,
    }


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Process one object and append one custody event."""

    required = ("matter_id", "object_key", "evidence_id", "actor", "occurred_at")
    missing = [name for name in required if not event.get(name)]
    if missing:
        return _refusal(
            "incomplete_event_request",
            "The Lambda request is missing required metadata.",
            f"Provide: {', '.join(missing)}.",
        )
    bucket = os.environ["EVIDENCE_BUCKET"]
    s3 = boto3.client("s3")
    table = boto3.resource("dynamodb").Table(os.environ["CUSTODY_TABLE"])
    try:
        body = s3.get_object(Bucket=bucket, Key=event["object_key"])["Body"].read()
        content_hash = sha256_bytes(body)
        previous = table.query(
            KeyConditionExpression=Key("matter_id").eq(event["matter_id"]),
            ProjectionExpression="event_hash, occurred_at, event_id",
        ).get("Items", [])
        event_id = sha256_json(
            {
                "matter_id": event["matter_id"],
                "evidence_id": event["evidence_id"],
                "content_sha256": content_hash,
            }
        )[:24]
        previous_item = max(
            previous,
            key=lambda item: (item.get("occurred_at", ""), item.get("event_id", "")),
            default=None,
        )
        previous_hash = previous_item.get("event_hash") if previous_item else None
        custody_event = make_event(
            event_id=event_id,
            matter_id=event["matter_id"],
            evidence_id=event["evidence_id"],
            event_type="ingested",
            actor=event["actor"],
            occurred_at=event["occurred_at"],
            details={
                "object_key": event["object_key"],
                "content_sha256": content_hash,
                "size_bytes": len(body),
            },
            previous_event_hash=previous_hash,
        )
        table.put_item(
            Item={
                "matter_id": custody_event.matter_id,
                "event_id": custody_event.event_id,
                **custody_event.to_dict(),
            },
            ConditionExpression="attribute_not_exists(event_id)",
        )
        return {
            "status": "OK",
            "event_id": custody_event.event_id,
            "evidence_id": custody_event.evidence_id,
            "content_sha256": content_hash,
            "size_bytes": len(body),
        }
    except ClientError as error:
        error_code = error.response.get("Error", {}).get("Code")
        if error_code == "ConditionalCheckFailedException":
            return _refusal(
                "duplicate_event",
                "The event id already exists in the custody ledger.",
                "Treat the replay as already recorded; do not create a new event.",
            )
        return _refusal(
            "aws_operation_failed",
            f"AWS rejected the bounded operation: {error_code or 'unknown_error'}.",
            "Inspect the deployment permissions and retry with the same event identity.",
        )
