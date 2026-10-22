from __future__ import annotations

import json
from pathlib import Path

from evidence_ledger.models import MatterRequest, Refusal
from evidence_ledger.pipeline import run_matter, verify_package


def request() -> MatterRequest:
    return MatterRequest(
        matter_id="matter-test-001",
        requested_by="synthetic-reviewer",
        purpose="test the deterministic collection path",
        authorised_at="2026-10-01T00:00:00Z",
        expires_at="2026-11-01T00:00:00Z",
    )


def test_same_inputs_produce_same_metadata(tmp_path: Path, demo_input_dir: Path) -> None:
    first = run_matter(
        request=request(),
        input_dir=demo_input_dir,
        output_dir=tmp_path / "first",
        as_of="2026-10-22T00:00:00Z",
    )
    second = run_matter(
        request=request(),
        input_dir=demo_input_dir,
        output_dir=tmp_path / "second",
        as_of="2026-10-22T00:00:00Z",
    )
    assert not isinstance(first, Refusal)
    assert not isinstance(second, Refusal)
    first_manifest = json.loads(
        (Path(first.package_path) / "manifest.json").read_text(encoding="utf-8")
    )
    second_manifest = json.loads(
        (Path(second.package_path) / "manifest.json").read_text(encoding="utf-8")
    )
    first_manifest["package_path"] = None
    second_manifest["package_path"] = None
    assert first_manifest == second_manifest


def test_totals_reconcile(tmp_path: Path, demo_input_dir: Path) -> None:
    result = run_matter(
        request=request(),
        input_dir=demo_input_dir,
        output_dir=tmp_path,
        as_of="2026-10-22T00:00:00Z",
    )
    assert not isinstance(result, Refusal)
    assert result.totals.input_count == result.totals.output_count
    assert (
        result.totals.ingested_count
        + result.totals.skipped_count
        + result.totals.failed_count
        == result.totals.output_count
    )


def test_tampered_object_is_refused(tmp_path: Path, demo_input_dir: Path) -> None:
    result = run_matter(
        request=request(),
        input_dir=demo_input_dir,
        output_dir=tmp_path,
        as_of="2026-10-22T00:00:00Z",
    )
    assert not isinstance(result, Refusal)
    object_path = next((Path(result.package_path) / "objects").iterdir())
    object_path.write_text("tampered synthetic content", encoding="utf-8")
    verification = verify_package(Path(result.package_path))
    assert isinstance(verification, Refusal)
    assert verification.code == "object_tampered"


def test_expired_authorization_refuses(tmp_path: Path, demo_input_dir: Path) -> None:
    result = run_matter(
        request=request(),
        input_dir=demo_input_dir,
        output_dir=tmp_path,
        as_of="2026-12-01T00:00:00Z",
    )
    assert isinstance(result, Refusal)
    assert result.code == "authorization_expired_or_not_yet_active"


def test_limit_is_visible_and_not_exhaustive(tmp_path: Path, demo_input_dir: Path) -> None:
    result = run_matter(
        request=request(),
        input_dir=demo_input_dir,
        output_dir=tmp_path,
        as_of="2026-10-22T00:00:00Z",
        limit=1,
    )
    assert not isinstance(result, Refusal)
    assert result.totals.truncated is True
    assert result.totals.limit == 1
    assert result.totals.input_count == 2
    assert result.totals.output_count == 1
    assert result.totals.unprocessed_count == 1
