"""Canonical serialisation rules used by hashes and release evidence.

1. Hashes must cover a stable byte representation, not a pretty-printed document.
2. Object keys are sorted so equivalent metadata has identical fingerprints.
3. JSON output is UTF-8 and newline-terminated only at the file boundary.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> bytes:
    """Return the stable JSON bytes used for all fingerprints."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    """Return the hexadecimal SHA-256 fingerprint for bytes."""

    return hashlib.sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    """Return the SHA-256 fingerprint of canonical JSON."""

    return sha256_bytes(canonical_json(value))
