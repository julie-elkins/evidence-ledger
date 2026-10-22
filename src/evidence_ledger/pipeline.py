"""The local deterministic evidence pipeline.

1. The caller supplies `as_of`; the pipeline never substitutes the current time.
2. Candidate paths are sorted and each receives exactly one explicit outcome.
3. The report contains metadata only; source bytes stay inside the package objects.
4. Verification must succeed before a package is described as clean.
5. A bounded `limit` is visible in totals and cannot masquerade as exhaustive work.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .canonical import canonical_json, sha256_bytes, sha256_json
from .ledger import make_event
from .models import (
    CustodyEvent,
    EvidenceOutcome,
    MatterRequest,
    OutcomeStatus,
    Refusal,
    RunReport,
    RunTotals,
    VerificationReport,
)


def _parse_time(value: str) -> datetime | Refusal:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return Refusal(
            code="invalid_timestamp",
            message="The timestamp is not valid ISO-8601 data.",
            guidance="Pass a UTC timestamp such as 2026-10-22T00:00:00Z.",
        )
    if parsed.tzinfo is None:
        return Refusal(
            code="timestamp_missing_timezone",
            message="The timestamp has no timezone.",
            guidance="Pass an explicit UTC timestamp ending in Z.",
        )
    return parsed.astimezone(timezone.utc)


def _validate_request(request: MatterRequest, as_of: str) -> Refusal | None:
    if not request.matter_id or not request.requested_by or not request.purpose:
        return Refusal(
            code="incomplete_request",
            message="The matter request is missing a required authorization field.",
            guidance="Provide matter_id, requested_by, and purpose.",
        )
    authorised_at = _parse_time(request.authorised_at)
    expires_at = _parse_time(request.expires_at)
    observed_at = _parse_time(as_of)
    if isinstance(authorised_at, Refusal):
        return authorised_at
    if isinstance(expires_at, Refusal):
        return expires_at
    if isinstance(observed_at, Refusal):
        return observed_at
    if expires_at <= authorised_at:
        return Refusal(
            code="invalid_authorization_window",
            message="The authorization expiry is not after its start.",
            guidance="Set expires_at later than authorised_at.",
        )
    if not authorised_at <= observed_at < expires_at:
        return Refusal(
            code="authorization_expired_or_not_yet_active",
            message="The requested run is outside its authorization window.",
            guidance="Use an as_of timestamp inside the approved window or obtain a new request.",
        )
    return None


def _candidate_paths(input_dir: Path) -> list[Path]:
    return sorted(
        (path for path in input_dir.rglob("*") if path.is_file() or path.is_symlink()),
        key=lambda path: path.relative_to(input_dir).as_posix(),
    )


def _run_id(request: MatterRequest, as_of: str, input_paths: list[Path]) -> str:
    return sha256_json(
        {
            "matter": request.to_dict(),
            "as_of": as_of,
            "paths": [path.as_posix() for path in input_paths],
        }
    )[:24]


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical_json(value) + b"\n")


def run_matter(
    *,
    request: MatterRequest,
    input_dir: Path,
    output_dir: Path,
    as_of: str,
    actor: str = "local-runner",
    limit: int | None = None,
) -> RunReport | Refusal:
    """Run one bounded matter collection and write a metadata manifest."""

    refusal = _validate_request(request, as_of)
    if refusal:
        return refusal
    if not input_dir.is_dir():
        return Refusal(
            code="input_directory_missing",
            message="The input directory does not exist.",
            guidance="Create the synthetic input directory or pass a valid path.",
        )
    if limit is not None and limit < 1:
        return Refusal(
            code="invalid_limit",
            message="The input limit must be at least one.",
            guidance="Omit the limit for exhaustive processing or pass a positive integer.",
        )

    candidates = _candidate_paths(input_dir)
    selected = candidates if limit is None else candidates[:limit]
    run_id = _run_id(request, as_of, selected)
    package_dir = output_dir / "package"
    objects_dir = package_dir / "objects"
    if package_dir.exists():
        shutil.rmtree(package_dir)
    objects_dir.mkdir(parents=True, exist_ok=True)

    outcomes: list[EvidenceOutcome] = []
    events: list[CustodyEvent] = []
    previous_event_hash: str | None = None

    for index, path in enumerate(selected):
        relative_path = path.relative_to(input_dir).as_posix()
        evidence_id = sha256_json(
            {"matter_id": request.matter_id, "relative_path": relative_path}
        )[:24]
        if path.is_symlink():
            outcome = EvidenceOutcome(
                evidence_id=evidence_id,
                relative_path=relative_path,
                status=OutcomeStatus.SKIPPED,
                content_sha256=None,
                size_bytes=None,
                reason="symlink_not_allowed",
            )
        else:
            try:
                content = path.read_bytes()
                content_hash = sha256_bytes(content)
                (objects_dir / evidence_id).write_bytes(content)
                outcome = EvidenceOutcome(
                    evidence_id=evidence_id,
                    relative_path=relative_path,
                    status=OutcomeStatus.INGESTED,
                    content_sha256=content_hash,
                    size_bytes=len(content),
                    reason=None,
                )
            except OSError:
                outcome = EvidenceOutcome(
                    evidence_id=evidence_id,
                    relative_path=relative_path,
                    status=OutcomeStatus.FAILED,
                    content_sha256=None,
                    size_bytes=None,
                    reason="read_failed",
                )

        event = make_event(
            event_id=f"{run_id}-{index:06d}",
            matter_id=request.matter_id,
            evidence_id=evidence_id,
            event_type=outcome.status.value.lower(),
            actor=actor,
            occurred_at=as_of,
            details={
                "relative_path": relative_path,
                "reason": outcome.reason,
                "size_bytes": outcome.size_bytes,
            },
            previous_event_hash=previous_event_hash,
        )
        previous_event_hash = event.event_hash
        events.append(event)
        outcomes.append(outcome)

    ingested_count = sum(
        outcome.status is OutcomeStatus.INGESTED for outcome in outcomes
    )
    skipped_count = sum(outcome.status is OutcomeStatus.SKIPPED for outcome in outcomes)
    failed_count = sum(outcome.status is OutcomeStatus.FAILED for outcome in outcomes)
    totals = RunTotals(
        input_count=len(candidates),
        ingested_count=ingested_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        output_count=len(outcomes),
        unprocessed_count=len(candidates) - len(selected),
        truncated=limit is not None and len(candidates) > len(selected),
        limit=limit,
    )
    if totals.input_count != totals.output_count + totals.unprocessed_count:
        return Refusal(
            code="unreconciled_totals",
            message="The run could not reconcile candidate inputs with outcomes.",
            guidance="Inspect the candidate enumeration and rerun before trusting the package.",
        )
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "matter": request.to_dict(),
        "as_of": as_of,
        "totals": totals.to_dict(),
        "outcomes": [outcome.to_dict() for outcome in outcomes],
        "custody_event_count": len(events),
        "content_policy": "Source bytes are confined to package/objects and are not reported.",
    }
    _write_json(package_dir / "manifest.json", manifest)
    (package_dir / "custody.jsonl").write_text(
        "".join(json.dumps(event.to_dict(), sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )
    return RunReport(
        run_id=run_id,
        matter=request,
        as_of=as_of,
        totals=totals,
        outcomes=tuple(outcomes),
        custody_event_count=len(events),
        package_path=str(package_dir),
    )


def verify_package(package_dir: Path) -> VerificationReport | Refusal:
    """Verify manifest totals, object fingerprints, and the custody chain."""

    manifest_path = package_dir / "manifest.json"
    custody_path = package_dir / "custody.jsonl"
    objects_dir = package_dir / "objects"
    if not manifest_path.is_file() or not custody_path.is_file() or not objects_dir.is_dir():
        return Refusal(
            code="package_incomplete",
            message="The package is missing a manifest, custody ledger, or objects directory.",
            guidance="Regenerate the package with the local runner.",
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        events = [
            json.loads(line)
            for line in custody_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
    except (OSError, json.JSONDecodeError):
        return Refusal(
            code="package_unreadable",
            message="The package metadata is not valid JSON.",
            guidance="Regenerate the package rather than repairing it in place.",
        )
    totals = manifest.get("totals", {})
    outcomes = manifest.get("outcomes", [])
    if totals.get("input_count") != (
        totals.get("output_count", 0) + totals.get("unprocessed_count", 0)
    ):
        return Refusal(
            code="totals_do_not_reconcile",
            message="The package totals do not reconcile to its outcomes.",
            guidance="Treat the package as incomplete and regenerate it.",
        )
    if len(events) != manifest.get("custody_event_count"):
        return Refusal(
            code="custody_count_mismatch",
            message="The custody event count does not match the manifest.",
            guidance="Treat the package as tampered or incomplete.",
        )

    outcomes_by_id = {outcome["evidence_id"]: outcome for outcome in outcomes}
    if set(event["evidence_id"] for event in events) != set(outcomes_by_id):
        return Refusal(
            code="custody_manifest_mismatch",
            message="The custody ledger does not cover exactly the manifest outcomes.",
            guidance="Regenerate the package from the original inputs.",
        )
    expected_previous: str | None = None
    for event in events:
        payload = {
            key: event[key]
            for key in (
                "event_id",
                "matter_id",
                "evidence_id",
                "event_type",
                "actor",
                "occurred_at",
                "details",
                "previous_event_hash",
            )
        }
        if event.get("previous_event_hash") != expected_previous:
            return Refusal(
                code="custody_chain_broken",
                message="The custody event chain is missing or out of order.",
                guidance="Regenerate the package from the original inputs.",
            )
        if event.get("event_hash") != sha256_json(payload):
            return Refusal(
                code="custody_event_tampered",
                message="A custody event fingerprint does not match its contents.",
                guidance="Regenerate the package from the original inputs.",
            )
        outcome = outcomes_by_id[event["evidence_id"]]
        if event.get("event_type") != outcome.get("status", "").lower():
            return Refusal(
                code="custody_outcome_mismatch",
                message="A custody event status does not match its manifest outcome.",
                guidance="Regenerate the package from the original inputs.",
            )
        expected_previous = event["event_hash"]

    checked_objects = 0
    expected_object_names: set[str] = set()
    for outcome in outcomes:
        if outcome.get("status") != OutcomeStatus.INGESTED.value:
            continue
        evidence_id = outcome["evidence_id"]
        expected_object_names.add(evidence_id)
        object_path = objects_dir / evidence_id
        if not object_path.is_file():
            return Refusal(
                code="object_missing",
                message="An ingested evidence object is missing from the package.",
                guidance="Regenerate the package from the original inputs.",
            )
        if sha256_bytes(object_path.read_bytes()) != outcome.get("content_sha256"):
            return Refusal(
                code="object_tampered",
                message="An evidence object fingerprint does not match the manifest.",
                guidance="Regenerate the package from the original inputs.",
            )
        checked_objects += 1
    actual_object_names = {path.name for path in objects_dir.iterdir() if path.is_file()}
    if actual_object_names != expected_object_names:
        return Refusal(
            code="unexpected_objects",
            message="The package contains an object that is not described by its manifest.",
            guidance="Regenerate the package from the original inputs.",
        )
    return VerificationReport(
        package_path=str(package_dir),
        verified=True,
        checked_objects=checked_objects,
        checked_events=len(events),
        message="Package verified; this proves package integrity, not legal relevance.",
    )
