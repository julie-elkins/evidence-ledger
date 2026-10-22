from pathlib import Path


def test_template_contains_required_security_controls() -> None:
    template = (Path(__file__).parents[2] / "infra" / "template.yaml").read_text()
    required_fragments = [
        "ObjectLockEnabled: true",
        "BlockPublicAcls: true",
        "BlockPublicPolicy: true",
        "IgnorePublicAcls: true",
        "RestrictPublicBuckets: true",
        "SSEAlgorithm: AES256",
        "Status: Enabled",
        "aws:SecureTransport: false",
        "NotificationConfiguration:",
        "s3:ObjectCreated:*",
        "Value: incoming/",
        "MaximumRetryAttempts: 2",
        "MaximumEventAgeInSeconds: 3600",
        "SqsManagedSseEnabled: true",
        "sqs:SendMessage",
        "dynamodb:PutItem",
        "dynamodb:Query",
    ]
    for fragment in required_fragments:
        assert fragment in template, fragment


def test_lambda_role_has_no_delete_or_update_actions() -> None:
    template = (Path(__file__).parents[2] / "infra" / "template.yaml").read_text()
    assert "dynamodb:DeleteItem" not in template
    assert "dynamodb:UpdateItem" not in template
    assert "s3:DeleteObject" not in template
    assert "logs:CreateLogGroup" not in template
