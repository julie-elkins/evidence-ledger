"""Numbered design rules for the Evidence Ledger data model.

1. A failed or skipped input is a record, not an absence.
2. Reports carry denominators and reconcile their totals.
3. Refusals are structured results so callers can name the cheapest remedy.
4. Records are immutable value objects; state changes append events instead.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class OutcomeStatus(StrEnum):
    """The only permitted outcome states for a candidate input."""

    INGESTED = "INGESTED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class Refusal:
    """A safe refusal that tells the caller what to repair."""

    code: str
    message: str
    guidance: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class MatterRequest:
    """The bounded authorization and scope for one synthetic matter run."""

    matter_id: str
    requested_by: str
    purpose: str
    authorised_at: str
    expires_at: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceOutcome:
    """Metadata about one candidate input; never stores source bytes."""

    evidence_id: str
    relative_path: str
    status: OutcomeStatus
    content_sha256: str | None
    size_bytes: int | None
    reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "relative_path": self.relative_path,
            "status": self.status.value,
            "content_sha256": self.content_sha256,
            "size_bytes": self.size_bytes,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class CustodyEvent:
    """One append-only event in the custody hash chain."""

    event_id: str
    matter_id: str
    evidence_id: str
    event_type: str
    actor: str
    occurred_at: str
    details: dict[str, Any]
    previous_event_hash: str | None
    event_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunTotals:
    """Reconciled counts for one run."""

    input_count: int
    ingested_count: int
    skipped_count: int
    failed_count: int
    output_count: int
    unprocessed_count: int
    truncated: bool
    limit: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunReport:
    """Metadata-only report for a completed local run."""

    run_id: str
    matter: MatterRequest
    as_of: str
    totals: RunTotals
    outcomes: tuple[EvidenceOutcome, ...]
    custody_event_count: int
    package_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "matter": self.matter.to_dict(),
            "as_of": self.as_of,
            "totals": self.totals.to_dict(),
            "outcomes": [outcome.to_dict() for outcome in self.outcomes],
            "custody_event_count": self.custody_event_count,
            "package_path": self.package_path,
        }


@dataclass(frozen=True)
class VerificationReport:
    """Metadata-only result of verifying a package."""

    package_path: str
    verified: bool
    checked_objects: int
    checked_events: int
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
