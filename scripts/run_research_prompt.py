"""Run one ResearchRequest through RD-Lab AutoGen (Gemini GroupChat path). Usage: python scripts/run_research_prompt.py \"Your question.\""""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_research_prompt.py \"Research question text.\"")
        return 1

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    key = (os.getenv("GOOGLE_API_KEY") or "").strip()
    if not key or key == "change-me":
        print("ERROR: Set GOOGLE_API_KEY in .env.")
        return 1

    os.environ["PROVIDER_MODE"] = "GEMINI"
    os.environ["CLOUD_LIGHT_MODEL_NAME"] = "gemini-2.5-flash-lite"
    os.environ["CLOUD_HEAVY_MODEL_NAME"] = "gemini-2.5-flash"
    os.environ.setdefault("AUTOGEN_REQUEST_TIMEOUT_SECONDS", "120")

    sys.path.insert(0, str(ROOT / "rd-lab" / "src"))
    sys.path.insert(0, str(ROOT / "shared-schemas" / "src"))

    from rd_lab.autogen_research import run_autogen_with_pydantic_retries
    from rd_lab.models.research_request import ResearchRequest

    question = " ".join(sys.argv[1:]).strip()
    request = ResearchRequest(
        correlation_id=UUID("33333333-3333-3333-3333-333333333333"),
        research_question=question,
        rationale="User-requested prompt test via scripts/run_research_prompt.py.",
        constraints={},
    )

    with tempfile.TemporaryDirectory() as tmp:
        spinalcord = Path(tmp) / "spinalcord"
        rhythms = Path(tmp) / "rhythms"
        for sub in ("requests", "discoveries", "results", "errors", "debates"):
            (spinalcord / sub).mkdir(parents=True, exist_ok=True)
        rhythms.mkdir(parents=True, exist_ok=True)

        print("Running AutoGen (Gemini GroupChat)...")
        outcome = run_autogen_with_pydantic_retries(
            request=request,
            spinalcord_root=str(spinalcord),
            rhythms_root=str(rhythms),
        )

        if outcome.success and outcome.discovery:
            d = outcome.discovery
            print("\n--- ResearchDiscovery (summary) ---")
            print(json.dumps(d.model_dump(mode="json"), indent=2, default=str))
            return 0

        print("FAIL:", outcome.last_error)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
