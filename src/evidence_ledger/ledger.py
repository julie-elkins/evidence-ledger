"""Append-only custody event construction.

1. The event hash covers the previous event hash and the complete event payload.
2. Event details contain identifiers and measurements, never source content.
3. Event order is explicit; a missing or reordered event must fail verification.
"""

from __future__ import annotations

from typing import Any

from .canonical import sha256_json
from .models import CustodyEvent


def make_event(
    *,
    event_id: str,
    matter_id: str,
    evidence_id: str,
    event_type: str,
    actor: str,
    occurred_at: str,
    details: dict[str, Any],
    previous_event_hash: str | None,
) -> CustodyEvent:
    """Construct one immutable event with a chained fingerprint."""

    payload = {
        "event_id": event_id,
        "matter_id": matter_id,
        "evidence_id": evidence_id,
        "event_type": event_type,
        "actor": actor,
        "occurred_at": occurred_at,
        "details": details,
        "previous_event_hash": previous_event_hash,
    }
    return CustodyEvent(
        **payload,
        event_hash=sha256_json(payload),
    )
