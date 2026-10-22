"""Command-line boundary for the deterministic local workflow."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .models import MatterRequest, Refusal
from .pipeline import run_matter, verify_package

LOGGER = logging.getLogger("evidence_ledger")
LOGGER.addHandler(logging.NullHandler())
LOGGER.propagate = False

DEMO_AS_OF = "2026-10-22T00:00:00Z"


def _demo_input_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "examples" / "good-matter" / "input"


def _print_result(result: object) -> int:
    if isinstance(result, Refusal):
        print(json.dumps({"status": "REFUSED", **result.to_dict()}, sort_keys=True))
        return 2
    print(json.dumps({"status": "OK", **result.to_dict()}, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Evidence Ledger local path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="Run the committed synthetic fixture.")
    demo.add_argument("--output", type=Path, required=True)
    demo.add_argument("--limit", type=int)

    verify = subparsers.add_parser("verify", help="Verify a generated package.")
    verify.add_argument("--package", type=Path, required=True)
    return parser


def main() -> int:
    """Run a command and return a shell exit code."""

    logging.basicConfig(level=logging.WARNING)
    args = _build_parser().parse_args()
    if args.command == "demo":
        request = MatterRequest(
            matter_id="matter-demo-001",
            requested_by="synthetic-reviewer",
            purpose="demonstrate controlled evidence collection",
            authorised_at="2026-10-01T00:00:00Z",
            expires_at="2026-11-01T00:00:00Z",
        )
        result = run_matter(
            request=request,
            input_dir=_demo_input_dir(),
            output_dir=args.output,
            as_of=DEMO_AS_OF,
            limit=args.limit,
        )
        return _print_result(result)
    return _print_result(verify_package(args.package))
