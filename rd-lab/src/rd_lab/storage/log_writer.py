"""
Rationale: RD Lab requires its own sovereign "Rhythms" (local-only audit logs).

How:
- Provides a simple JSONL appender consistent with Trinity's rhythm logger,
  without importing Trinity code.

Contracts:
- Must not serialize secrets in rhythm payloads.
- Uses `RhythmEvent` from `shared_schemas`.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from shared_schemas.rhythm_event import RhythmEvent, RhythmEventType


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def rhythm_log_path(rhythms_root: str, hemisphere: str) -> Path:
    """
    Rationale: Deterministic rhythm file location.
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
    Rationale: Single function to prevent unsafe log payloads.
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

