from __future__ import annotations

from pathlib import Path

from evidence_ledger.models import MatterRequest, Refusal
from evidence_ledger.pipeline import run_matter


def test_manifest_does_not_contain_source_fixture_text(
    tmp_path: Path, demo_input_dir: Path
) -> None:
    result = run_matter(
        request=MatterRequest(
            matter_id="matter-invariant-001",
            requested_by="synthetic-reviewer",
            purpose="test metadata-only reporting",
            authorised_at="2026-10-01T00:00:00Z",
            expires_at="2026-11-01T00:00:00Z",
        ),
        input_dir=demo_input_dir,
        output_dir=tmp_path,
        as_of="2026-10-22T00:00:00Z",
    )
    assert not isinstance(result, Refusal)
    manifest = (Path(result.package_path) / "manifest.json").read_text(encoding="utf-8")
    assert "Synthetic record A" not in manifest
    assert "Synthetic record B" not in manifest
