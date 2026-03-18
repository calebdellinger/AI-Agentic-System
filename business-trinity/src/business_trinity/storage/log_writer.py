"""
Rationale: Local-only "Rhythms" provide sovereign audit trails.

How:
- Appends rhythm events as JSON Lines to a mounted file path.

Contracts:
- Uses `RhythmEvent` from `shared_schemas`.
- Must not write secrets to disk.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from shared_schemas.rhythm_event import RhythmEvent, RhythmEventType


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def rhythm_log_path(rhythms_root: str, hemisphere: str) -> Path:
    """
    Rationale: Deterministic file naming helps auditors locate event streams.

    Contracts:
    - `hemisphere` is a label like `trinity` or `lab`.
    """

    return Path(rhythms_root) / f"{hemisphere}.jsonl"


def append_rhythm_event(
    *,
    rhythms_root: str,
    hemisphere: str,
    event_type: RhythmEventType,
    payload: Optional[dict[str, Any]] = None,
    correlation_id: Optional[UUID] = None,
    record_id: Optional[UUID] = None,
) -> None:
    """
    Rationale: Centralize rhythm event serialization so logging stays safe.
    """

    path = rhythm_log_path(rhythms_root, hemisphere)
    _ensure_parent_dir(path)

    event = RhythmEvent(
        event_type=event_type,
        payload=payload or {},
        correlation_id=correlation_id,
        record_id=record_id,
    )

    line = json.dumps(event.model_dump(mode="json"), sort_keys=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

