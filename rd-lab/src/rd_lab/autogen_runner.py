"""
Rationale: RD Lab is responsible for open-ended innovation in a sandbox.

How (scaffolding stage):
- Ensures spinalcord subdirectories exist.
- Emits a local rhythm event that Lab started.
- Does not yet run AutoGen; this file is the placeholder entrypoint.

Contracts:
- Must write rhythms to a mounted local volume only.
- Must communicate across hemispheres via schema-validated JSON files in
  `spinalcord/discoveries` (no network handoff).
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from rd_lab.bridge.inbox import iter_requests
from rd_lab.storage.log_writer import append_rhythm_event


def _spinalcord_subdirs(spinalcord_root: str) -> dict[str, Path]:
    root = Path(spinalcord_root)
    return {
        "requests": root / "requests",
        "discoveries": root / "discoveries",
        "results": root / "results",
        "errors": root / "errors",
    }


def ensure_spinalcord_dirs(spinalcord_root: str) -> None:
    for p in _spinalcord_subdirs(spinalcord_root).values():
        p.mkdir(parents=True, exist_ok=True)


def main() -> None:
    spinalcord_root = os.getenv("SPINALCORD_ROOT", "/spinalcord")
    rhythms_root = os.getenv("RHYTHM_STORAGE_ROOT", "/rhythms")

    ensure_spinalcord_dirs(spinalcord_root)

    append_rhythm_event(
        rhythms_root=rhythms_root,
        hemisphere="lab",
        event_type="#INFO",
        payload={"msg": "RD Lab scaffold started"},
    )

    # Scaffolding: keep the container alive while we implement AutoGen -> schema
    # discovery emission in Phase 3.
    while True:
        # We intentionally do not consume iter_requests() yet, since the
        # discovery-generation logic is not part of scaffolding.
        _ = list(iter_requests(spinalcord_root))
        time.sleep(10)


if __name__ == "__main__":
    main()

