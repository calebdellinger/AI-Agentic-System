"""
Rationale: Inbox reads Lab input work items from the shared volume.

How (scaffolding stage):
- Defines the read contract for `ResearchRequest`-like objects.

Contracts:
- Must read from `SPINALCORD_ROOT/requests`.
- Must not call Trinity over the network; exchange is file/volume based.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator


def iter_request_files(spinalcord_root: str) -> Iterator[tuple[Path, dict[str, Any]]]:
    """
    Rationale: File-based queue semantics.

    How:
    - Reads any `*.json` files found under `requests/`.
    """

    requests_dir = Path(spinalcord_root) / "requests"
    if not requests_dir.exists():
        return

    for p in sorted(requests_dir.glob("*.json")):
        yield p, json.loads(p.read_text(encoding="utf-8"))


def iter_requests(spinalcord_root: str) -> Iterator[dict[str, Any]]:
    """
    Rationale: Backwards-compatible adapter for scaffolding code.
    """

    for _p, data in iter_request_files(spinalcord_root):
        yield data

