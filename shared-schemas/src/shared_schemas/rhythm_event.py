"""
Rationale: "Rhythms" are local-only event logs for sovereignty and auditing.

How:
- Defines the schema for rhythm events appended to local JSONL files.

Contracts:
- No secrets should be stored in `payload`.
- Events may include `#SYSTEM_ESCALATION` to record fallback decisions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


RhythmEventType = Literal[
    "#SYSTEM_VALIDATION_FAILURE",
    "#SYSTEM_ESCALATION",
    "#DECISION_RATIONALE_WRITTEN",
    "#WORKORDER_CREATED",
    "#WORKORDER_RESULT",
    "#INFO",
]


class RhythmEvent(BaseModel):
    """
    Rationale: Standardize rhythm event structure.

    How:
    - Enables deterministic parsing of JSONL logs by any future tool.
    """

    event_type: RhythmEventType
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    correlation_id: Optional[UUID] = None
    record_id: Optional[UUID] = None

    # Keep payload small and secret-free.
    payload: dict[str, Any] = Field(default_factory=dict)

