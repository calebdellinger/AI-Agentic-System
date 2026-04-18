"""
Rationale: Trinity orchestrator loop is responsible for:
- Consuming `ResearchDiscovery` records from the shared `spinalcord` volume.
- Writing `DecisionRecord` rationale rhythms before any execution dispatch.
- Creating `WorkOrder` intents for n8n (external actions).

How (scaffolding stage):
- Creates the expected spinalcord subdirectories.
- Emits a local startup rhythm event.
- Does not yet perform CrewAI/LLM execution; this file is a placeholder for
  Phase 3 integration.

Contracts:
- Must write rhythms to `RHYTHM_STORAGE_ROOT` only (local volume).
- Must read/write only via mounted `SPINALCORD_ROOT`.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from shared_schemas.rhythm_event import RhythmEventType

from business_trinity.storage.log_writer import append_rhythm_event
from shared.company_knowledge.paths import summarize_knowledge_mount


def _spinalcord_subdirs(spinalcord_root: str) -> dict[str, Path]:
    root = Path(spinalcord_root)
    return {
        "requests": root / "requests",
        "discoveries": root / "discoveries",
        "results": root / "results",
        "errors": root / "errors",
    }


def ensure_spinalcord_dirs(spinalcord_root: str) -> None:
    """
    Rationale: Deterministic filesystem contracts.

    How: Creates required directories so the lab/trinity handoff works
    immediately.
    """

    for p in _spinalcord_subdirs(spinalcord_root).values():
        p.mkdir(parents=True, exist_ok=True)


def main_loop() -> None:
    """
    Rationale: Single process entrypoint for container execution.
    """

    spinalcord_root = os.getenv("SPINALCORD_ROOT", "/spinalcord")
    rhythms_root = os.getenv("RHYTHM_STORAGE_ROOT", "/rhythms")

    ensure_spinalcord_dirs(spinalcord_root)

    append_rhythm_event(
        rhythms_root=rhythms_root,
        hemisphere="trinity",
        event_type="#INFO",
        payload={"msg": "Trinity orchestrator scaffold started"},
    )
    append_rhythm_event(
        rhythms_root=rhythms_root,
        hemisphere="trinity",
        event_type="#INFO",
        payload={
            "msg": "Company knowledge mount (shared with RD-Lab)",
            **summarize_knowledge_mount(),
        },
    )

    # Scaffolding: keep the container alive while we build Phase 2/3 loops.
    # Rationale: Allows operators to validate networking/volumes first.
    while True:
        time.sleep(10)


if __name__ == "__main__":
    main_loop()

