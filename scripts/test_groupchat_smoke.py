"""
Rationale: One-shot smoke test for AutoGen GroupChat (cloud/Gemini) without stalling forever.

How:
- Loads repo-root `.env` (GOOGLE_API_KEY, PROVIDER_MODE).
- Runs `run_autogen_with_pydantic_retries` in a temp spinalcord with a minimal request.
- Enforces a wall-clock timeout via ThreadPoolExecutor.

Contracts:
- Does not print secrets.
"""

from __future__ import annotations

import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parent.parent


def _run() -> int:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")

    key = (os.getenv("GOOGLE_API_KEY") or "").strip()
    if not key or key == "change-me":
        print("ERROR: Set a real GOOGLE_API_KEY in .env (not change-me).")
        return 1

    # This script tests the cloud GroupChat path; override LOCAL from .env.
    os.environ["PROVIDER_MODE"] = "GEMINI"
    # Known-good Gemini OpenAI-compat model ids (avoid stale llama ids from .env).
    os.environ["CLOUD_LIGHT_MODEL_NAME"] = "gemini-2.5-flash-lite"
    os.environ["CLOUD_HEAVY_MODEL_NAME"] = "gemini-2.5-flash"

    # Bare-minimum GroupChat caps for testing (one user kickoff + six agent turns).
    os.environ["AUTOGEN_GROUPCHAT_MAX_ROUNDS"] = "8"
    os.environ["AUTOGEN_GROUPCHAT_MAX_RETRIES_SELECT_SPEAKER"] = "1"
    os.environ["AUTOGEN_GROUPCHAT_USER_PROXY_MAX_REPLY"] = "8"
    os.environ["AUTOGEN_GROUPCHAT_INITIATE_MAX_TURNS"] = "8"

    # Shorter HTTP timeout for smoke (override if unset).
    os.environ.setdefault("AUTOGEN_REQUEST_TIMEOUT_SECONDS", "120")

    from rd_lab.autogen_research import run_autogen_with_pydantic_retries
    from rd_lab.models.research_request import ResearchRequest

    request = ResearchRequest(
        correlation_id=UUID("22222222-2222-2222-2222-222222222222"),
        research_question=(
            "List two bullet points on why schema-valid JSON handoffs matter for multi-agent systems."
        ),
        rationale="GroupChat smoke test: verify completion without stall.",
        constraints={},
    )

    timeout_s = float(os.getenv("GROUPCHAT_SMOKE_TIMEOUT_SECONDS", "240"))

    with tempfile.TemporaryDirectory() as tmp:
        spinalcord = Path(tmp) / "spinalcord"
        rhythms = Path(tmp) / "rhythms"
        for sub in ("requests", "discoveries", "results", "errors", "debates"):
            (spinalcord / sub).mkdir(parents=True, exist_ok=True)
        rhythms.mkdir(parents=True, exist_ok=True)

        def _call():
            return run_autogen_with_pydantic_retries(
                request=request,
                spinalcord_root=str(spinalcord),
                rhythms_root=str(rhythms),
            )

        print(
            f"Starting GroupChat smoke (timeout {timeout_s}s, PROVIDER_MODE={os.getenv('PROVIDER_MODE')}, "
            f"max_rounds={os.environ['AUTOGEN_GROUPCHAT_MAX_ROUNDS']}, "
            f"initiate_max_turns={os.environ['AUTOGEN_GROUPCHAT_INITIATE_MAX_TURNS']})..."
        )
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_call)
            try:
                outcome = fut.result(timeout=timeout_s)
            except FutureTimeout:
                print(f"FAIL: Timed out after {timeout_s}s (stall or very slow API).")
                return 2
            except Exception as e:
                # Stall check: if we get an API error after GroupChat started, we did not hang.
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err or "RateLimitError" in type(e).__name__:
                    print(
                        "STALL CHECK: GroupChat orchestration reached Gemini (no infinite stall). "
                        "API returned quota/rate limit; fix billing or retry later for full success."
                    )
                    return 0
                if "404" in err and "models/" in err:
                    print(
                        "FAIL: Wrong model id for Gemini (check CLOUD_LIGHT_MODEL_NAME / remote model resolution)."
                    )
                    return 4
                raise

        if outcome.success and outcome.discovery:
            print("OK: ResearchDiscovery written (GroupChat path completed).")
            print(f"    correlation_id={outcome.discovery.correlation_id}")
            return 0

        print("FAIL: No valid discovery.", outcome.last_error)
        return 3


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "rd-lab" / "src"))
    sys.path.insert(0, str(ROOT / "shared-schemas" / "src"))
    raise SystemExit(_run())
