"""
Rationale: Let Trinity UI show specialist + synthesizer turns while a run is in flight.

How:
- Append-only JSONL under spinalcord/debates/{correlation_id}.jsonl
  (one line meta, then one line per agent turn). Flush after each line so
  Streamlit autorefresh can pick up partial debates.

Contracts:
- Must not log secrets. Content is capped to keep JSONL manageable.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_TURN_CHARS = 16_000


def _debates_dir(spinalcord_root: str) -> Path:
    p = Path(spinalcord_root) / "debates"
    p.mkdir(parents=True, exist_ok=True)
    return p


def debate_transcript_path(spinalcord_root: str, correlation_id: str) -> Path:
    return _debates_dir(spinalcord_root) / f"{correlation_id}.jsonl"


def debate_transcript_begin(
    *,
    spinalcord_root: str,
    request_id: str,
    correlation_id: str,
    research_question: str,
    attempt: int,
) -> Path:
    path = debate_transcript_path(spinalcord_root, correlation_id)
    meta: dict[str, Any] = {
        "type": "meta",
        "ts": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "correlation_id": str(correlation_id),
        "research_question": research_question[:2000],
        "attempt": attempt,
    }
    path.write_text(json.dumps(meta, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def debate_transcript_append_turn(
    *,
    spinalcord_root: str,
    correlation_id: str,
    agent: str,
    content: str,
    extra: dict[str, Any] | None = None,
) -> None:
    path = debate_transcript_path(spinalcord_root, correlation_id)
    if not path.exists():
        return
    text = (
        content
        if len(content) <= MAX_TURN_CHARS
        else content[: MAX_TURN_CHARS - 24] + "\n…(truncated)"
    )
    row: dict[str, Any] = {
        "type": "turn",
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "content": text,
    }
    if extra:
        row["extra"] = extra
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
