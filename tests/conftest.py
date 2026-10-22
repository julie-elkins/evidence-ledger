"""Shared synthetic fixtures for the local Evidence Ledger tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def demo_input_dir() -> Path:
    return Path(__file__).parents[1] / "examples" / "good-matter" / "input"
