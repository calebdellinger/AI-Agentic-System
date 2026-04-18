"""
Rationale: RD Lab is responsible for open-ended innovation in a sandbox.

How:
- Ensures spinalcord subdirectories exist.
- Emits local rhythm events for sovereignty and auditing.
- Consumes schema-validated requests from `spinalcord/requests/*.json`.
- Runs AutoGen debate locally and validates results with shared Pydantic
  schemas before writing `ResearchDiscovery` to `spinalcord/discoveries/`.

Contracts:
- Must write rhythms to a mounted local volume only.
- Must communicate across hemispheres via schema-validated JSON files in
  `spinalcord/discoveries` (no network handoff).
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from rd_lab.autogen_research import run_autogen_with_pydantic_retries, write_validation_error_artifact
from rd_lab.bridge.inbox import iter_request_files
from rd_lab.storage.log_writer import append_rhythm_event
from rd_lab.models.research_request import ResearchRequest
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
    append_rhythm_event(
        rhythms_root=rhythms_root,
        hemisphere="lab",
        event_type="#INFO",
        payload={
            "msg": "Company knowledge mount (shared with Trinity)",
            **summarize_knowledge_mount(),
        },
    )

    while True:
        # Consume requests from the file-based queue.
        for request_path, payload in iter_request_files(spinalcord_root):
            try:
                request = ResearchRequest.model_validate(payload)
            except Exception as e:  # noqa: BLE001
                # Validation failure at the request layer: write an error and
                # consume the file so we don't loop forever.
                req_id = payload.get("request_id")
                err_payload = {
                    "request_path": str(request_path),
                    "raw_payload": payload,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                }
                err_dir = Path(spinalcord_root) / "errors"
                err_dir.mkdir(parents=True, exist_ok=True)
                (err_dir / f"{req_id or request_path.stem}-request-invalid.json").write_text(
                    json.dumps(err_payload, sort_keys=True),
                    encoding="utf-8",
                )
                request_path.unlink(missing_ok=True)
                continue

            # Run AutoGen -> validate -> write discovery.
            outcome = run_autogen_with_pydantic_retries(
                request=request,
                spinalcord_root=spinalcord_root,
                rhythms_root=rhythms_root,
            )

            _ = write_validation_error_artifact(
                spinalcord_root=spinalcord_root,
                request=request,
                outcome=outcome,
            )

            # Consume request file on both success and failure to ensure
            # deterministic processing.
            done_dir = Path(spinalcord_root) / "results" / "consumed_requests"
            done_dir.mkdir(parents=True, exist_ok=True)
            done_path = done_dir / request_path.name
            if not done_path.exists():
                request_path.replace(done_path)

        time.sleep(10)


if __name__ == "__main__":
    main()

