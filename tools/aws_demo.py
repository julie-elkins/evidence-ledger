"""Run the bounded event-driven AWS demonstration against a deployed stack.

The script performs no deployment and no deletion. It uploads only the committed synthetic
fixture, waits for S3 to invoke the processor, replays the resulting request once, and
prints metadata-only responses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from time import monotonic, sleep
from typing import Any
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key


def _outputs(cloudformation: Any, stack_name: str) -> dict[str, str]:
    stacks = cloudformation.describe_stacks(StackName=stack_name)["Stacks"]
    if len(stacks) != 1:
        raise RuntimeError("Expected exactly one stack.")
    return {
        output["OutputKey"]: output["OutputValue"]
        for output in stacks[0].get("Outputs", [])
    }


def _wait_for_custody_event(
    table: Any,
    matter_id: str,
    object_key: str,
    content_sha256: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Wait for the asynchronous S3 notification to reach DynamoDB."""

    deadline = monotonic() + timeout_seconds
    while monotonic() < deadline:
        items = table.query(
            KeyConditionExpression=Key("matter_id").eq(matter_id),
        ).get("Items", [])
        matches = [
            item
            for item in items
            if item.get("details", {}).get("object_key") == object_key
            and item.get("details", {}).get("content_sha256") == content_sha256
        ]
        if matches:
            return matches[0]
        sleep(0.5)
    raise RuntimeError(f"Timed out waiting for S3 processing of {object_key}.")


def run_demo(
    stack_name: str,
    region: str,
    input_dir: Path,
    matter_id: str | None = None,
    timeout_seconds: float = 20.0,
) -> list[dict[str, Any]]:
    session = boto3.Session(region_name=region)
    cloudformation = session.client("cloudformation")
    s3 = session.client("s3")
    lambda_client = session.client("lambda")
    dynamodb = session.resource("dynamodb")
    outputs = _outputs(cloudformation, stack_name)
    bucket = outputs["EvidenceBucketName"]
    function_name = outputs["ProcessorFunctionName"]
    table = dynamodb.Table(outputs["CustodyTableName"])
    matter_id = matter_id or f"matter-aws-demo-{uuid4().hex[:12]}"
    responses: list[dict[str, Any]] = []
    for path in sorted(input_dir.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(input_dir).as_posix()
        object_key = f"incoming/{matter_id}/{relative_path}"
        content = path.read_bytes()
        content_sha256 = hashlib.sha256(content).hexdigest()
        s3.put_object(
            Bucket=bucket,
            Key=object_key,
            Body=content,
            ServerSideEncryption="AES256",
        )
        custody_event = _wait_for_custody_event(
            table=table,
            matter_id=matter_id,
            object_key=object_key,
            content_sha256=content_sha256,
            timeout_seconds=timeout_seconds,
        )
        replay = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(
                {
                    "matter_id": matter_id,
                    "object_key": object_key,
                    "evidence_id": custody_event["evidence_id"],
                    "actor": custody_event["actor"],
                    "occurred_at": custody_event["occurred_at"],
                }
            ).encode("utf-8"),
        )
        replay_body = json.loads(replay["Payload"].read())
        responses.append(
            {
                "relative_path": relative_path,
                "event_status": "OK",
                "event_id": custody_event["event_id"],
                "evidence_id": custody_event["evidence_id"],
                "content_sha256": content_sha256,
                "size_bytes": len(content),
                "replay_status": replay_body.get("code", replay_body.get("status")),
            }
        )
    print(json.dumps({"status": "OK", "matter_id": matter_id, "responses": responses}))
    return responses


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Evidence Ledger AWS demo.")
    parser.add_argument("--stack-name", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--input", type=Path, default=Path("examples/good-matter/input"))
    parser.add_argument("--matter-id")
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    args = parser.parse_args()
    run_demo(
        args.stack_name,
        args.region,
        args.input,
        matter_id=args.matter_id,
        timeout_seconds=args.timeout_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
