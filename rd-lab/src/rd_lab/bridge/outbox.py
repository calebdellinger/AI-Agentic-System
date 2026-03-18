"""
Rationale: Outbox writes Lab discoveries to the shared `spinalcord` volume.

How (scaffolding stage):
- Defines how to serialize and persist `ResearchDiscovery` objects as JSON
  under `spinalcord/discoveries/`.

Contracts:
- Must write schema-valid artifacts only.
- Writes to local mounted volume only; no network callbacks.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from shared_schemas.research_discovery import ResearchDiscovery


def _ensure_dir(spinalcord_root: str, subpath: str) -> Path:
    p = Path(spinalcord_root) / subpath
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_research_discovery(spinalcord_root: str, discovery: ResearchDiscovery) -> Path:
    """
    Rationale: Deterministic placement for Trinity consumption.

    How:
    - Writes a single JSON file named by `discovery_id`.
    - Does not overwrite existing files.

    Contracts:
    - `spinalcord_root/discoveries/` must be mounted into Trinity.
    """

    out_dir = _ensure_dir(spinalcord_root, "discoveries")
    out_path = out_dir / f"{discovery.discovery_id}.json"

    # Deterministic idempotency: if already present, do not overwrite.
    if out_path.exists():
        return out_path

    # Atomic write: write to a temp file then rename into place.
    tmp_path = out_dir / f".tmp-{discovery.discovery_id}-{uuid.uuid4().hex}.json"
    tmp_path.write_text(
        json.dumps(discovery.model_dump(mode="json"), sort_keys=True),
        encoding="utf-8",
    )
    tmp_path.replace(out_path)
    return out_path

