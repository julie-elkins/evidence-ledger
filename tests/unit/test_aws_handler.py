from __future__ import annotations

import os
from typing import Any

import pytest

from evidence_ledger import aws_handler


class Body:
    def read(self) -> bytes:
        return b"synthetic cloud object"


class FakeS3:
    def get_object(self, **kwargs: Any) -> dict[str, Body]:
        return {"Body": Body()}


class FakeTable:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    def query(self, **kwargs: Any) -> dict[str, list[dict[str, Any]]]:
        return {"Items": self.items}

    def put_item(self, *, Item: dict[str, Any], ConditionExpression: str) -> None:
        if any(item["event_id"] == Item["event_id"] for item in self.items):
            from botocore.exceptions import ClientError

            raise ClientError(
                {
                    "Error": {
                        "Code": "ConditionalCheckFailedException",
                        "Message": "duplicate",
                    }
                },
                "PutItem",
            )
        self.items.append(Item)


class FakeDynamo:
    def __init__(self, table: FakeTable) -> None:
        self.table = table

    def Table(self, name: str) -> FakeTable:
        return self.table


def test_lambda_writes_metadata_and_refuses_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    table = FakeTable()
    monkeypatch.setenv("EVIDENCE_BUCKET", "synthetic-bucket")
    monkeypatch.setenv("CUSTODY_TABLE", "synthetic-table")
    monkeypatch.setattr(aws_handler.boto3, "client", lambda name: FakeS3())
    monkeypatch.setattr(
        aws_handler.boto3,
        "resource",
        lambda name: FakeDynamo(table),
    )
    event = {
        "matter_id": "matter-001",
        "object_key": "incoming/matter-001/file.txt",
        "evidence_id": "evidence-001",
        "actor": "synthetic-reviewer",
        "occurred_at": "2026-10-22T00:00:00Z",
    }
    first = aws_handler.handler(event, None)
    second = aws_handler.handler(event, None)
    assert first["status"] == "OK"
    assert second["code"] == "duplicate_event"
    assert len(table.items) == 1


def test_lambda_refuses_missing_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVIDENCE_BUCKET", "synthetic-bucket")
    monkeypatch.setenv("CUSTODY_TABLE", "synthetic-table")
    result = aws_handler.handler({}, None)
    assert result["code"] == "incomplete_event_request"


def test_lambda_processes_s3_object_created_notification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    table = FakeTable()
    monkeypatch.setenv("EVIDENCE_BUCKET", "synthetic-bucket")
    monkeypatch.setenv("CUSTODY_TABLE", "synthetic-table")
    monkeypatch.setattr(aws_handler.boto3, "client", lambda name: FakeS3())
    monkeypatch.setattr(
        aws_handler.boto3,
        "resource",
        lambda name: FakeDynamo(table),
    )
    notification = {
        "Records": [
            {
                "eventName": "ObjectCreated:Put",
                "eventTime": "2026-10-22T00:00:00.000Z",
                "s3": {
                    "bucket": {"name": "synthetic-bucket"},
                    "object": {
                        "key": "incoming%2Fmatter-001%2Fcustodian%2Balice.txt",
                        "versionId": "version-001",
                    },
                },
            }
        ]
    }
    result = aws_handler.handler(notification, None)
    assert result["status"] == "OK"
    assert result["processed_count"] == 1
    assert result["results"][0]["status"] == "OK"
    assert table.items[0]["details"]["object_key"] == (
        "incoming/matter-001/custodian+alice.txt"
    )


def test_lambda_refuses_s3_object_outside_incoming_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EVIDENCE_BUCKET", "synthetic-bucket")
    monkeypatch.setenv("CUSTODY_TABLE", "synthetic-table")
    notification = {
        "Records": [
            {
                "eventName": "ObjectCreated:Put",
                "eventTime": "2026-10-22T00:00:00.000Z",
                "s3": {
                    "bucket": {"name": "synthetic-bucket"},
                    "object": {"key": "exports/report.json"},
                },
            }
        ]
    }
    result = aws_handler.handler(notification, None)
    assert result["status"] == "PARTIAL"
    assert result["results"][0]["code"] == "invalid_s3_notification"
