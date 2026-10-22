"""Run the bounded AWS demonstration against an already-deployed stack.

The script performs no deployment and no deletion. It uploads only the committed synthetic
fixture, invokes the processor sequentially, and prints metadata-only responses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import boto3


def _outputs(cloudformation: Any, stack_name: str) -> dict[str, str]:
    stacks = cloudformation.describe_stacks(StackName=stack_name)["Stacks"]
    if len(stacks) != 1:
        raise RuntimeError("Expected exactly one stack.")
    return {
        output["OutputKey"]: output["OutputValue"]
        for output in stacks[0].get("Outputs", [])
    }


def run_demo(stack_name: str, region: str, input_dir: Path) -> list[dict[str, Any]]:
    session = boto3.Session(region_name=region)
    cloudformation = session.client("cloudformation")
    s3 = session.client("s3")
    lambda_client = session.client("lambda")
    outputs = _outputs(cloudformation, stack_name)
    bucket = outputs["EvidenceBucketName"]
    function_name = outputs["ProcessorFunctionName"]
    matter_id = "matter-aws-demo-001"
    actor = "synthetic-reviewer"
    occurred_at = "2026-10-22T00:00:00Z"
    responses: list[dict[str, Any]] = []
    for path in sorted(input_dir.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(input_dir).as_posix()
        object_key = f"incoming/{matter_id}/{relative_path}"
        s3.put_object(
            Bucket=bucket,
            Key=object_key,
            Body=path.read_bytes(),
            ServerSideEncryption="AES256",
        )
        evidence_id = hashlib.sha256(
            json.dumps(
                {"matter_id": matter_id, "relative_path": relative_path},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:24]
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(
                {
                    "matter_id": matter_id,
                    "object_key": object_key,
                    "evidence_id": evidence_id,
                    "actor": actor,
                    "occurred_at": occurred_at,
                }
            ).encode("utf-8"),
        )
        body = json.loads(response["Payload"].read())
        responses.append(
            {
                "relative_path": relative_path,
                "lambda_status_code": response["StatusCode"],
                "result": body,
            }
        )
    print(json.dumps({"status": "OK", "matter_id": matter_id, "responses": responses}))
    return responses


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Evidence Ledger AWS demo.")
    parser.add_argument("--stack-name", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--input", type=Path, default=Path("examples/good-matter/input"))
    args = parser.parse_args()
    run_demo(args.stack_name, args.region, args.input)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
