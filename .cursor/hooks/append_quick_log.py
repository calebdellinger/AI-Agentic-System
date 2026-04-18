#!/usr/bin/env python3
"""
Append a short progress note to a single markdown log on each agent stop event.

Behavior:
- Reads hook JSON from stdin.
- Extracts the most useful assistant completion text available.
- Converts it to a concise 1-3 sentence summary.
- Appends the summary to docs/QUICK_PROGRESS_LOG.md.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    # .cursor/hooks/append_quick_log.py -> project root is two levels up.
    return Path(__file__).resolve().parents[2]


def _load_event_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return {}


def _first_meaningful_string(node: Any) -> str | None:
    if isinstance(node, str):
        text = node.strip()
        return text if len(text) >= 20 else None
    if isinstance(node, dict):
        preferred_keys = (
            "final_response",
            "assistant_response",
            "response",
            "message",
            "text",
            "output",
            "content",
        )
        for key in preferred_keys:
            value = node.get(key)
            extracted = _first_meaningful_string(value)
            if extracted:
                return extracted
        for value in node.values():
            extracted = _first_meaningful_string(value)
            if extracted:
                return extracted
    elif isinstance(node, list):
        for item in node:
            extracted = _first_meaningful_string(item)
            if extracted:
                return extracted
    return None


def _strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    lines: list[str] = []
    for line in text.splitlines():
        line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)
        line = re.sub(r"^\s*[-*+]\s+", "", line)
        line = re.sub(r"^\s*\d+\.\s+", "", line)
        line = line.strip()
        if line:
            lines.append(line)
    cleaned = " ".join(lines)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _summarize(text: str) -> str:
    cleaned = _strip_markdown(text)
    if not cleaned:
        return "Completed a meaningful project update."

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
    selected: list[str] = []
    for sentence in sentences:
        if len(selected) == 3:
            break
        selected.append(sentence)

    if not selected:
        clipped = cleaned[:220].rstrip()
        return clipped + ("." if not clipped.endswith((".", "!", "?")) else "")

    summary = " ".join(selected)
    if not summary.endswith((".", "!", "?")):
        summary += "."
    return summary


def _ensure_log_file(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Quick Progress Log\n\n"
        "A rolling 1-3 sentence summary of major completed work.\n\n",
        encoding="utf-8",
    )


def main() -> int:
    payload = _load_event_payload()
    extracted = _first_meaningful_string(payload) or ""
    summary = _summarize(extracted)

    project_root = _project_root()
    log_path = project_root / "docs" / "QUICK_PROGRESS_LOG.md"
    _ensure_log_file(log_path)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"## {timestamp}\n")
        f.write(f"- {summary}\n\n")

    # stop hooks can run silently; return empty JSON object for compatibility.
    sys.stdout.write("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
