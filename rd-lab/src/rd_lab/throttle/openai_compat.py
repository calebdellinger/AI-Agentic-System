"""
Rationale: AutoGen's agents only need an OpenAI-compatible Chat Completions API.

How:
- Resolve `base_url`, `api_key`, and pass through `model` + `temperature` for every agent.
- Local: Ollama/vLLM (`VLLM_BASE_URL` + placeholder api key).
- Gemini: Google's OpenAI compatibility endpoint + `GOOGLE_API_KEY`.
- Anything else: set `AUTOGEN_OPENAI_BASE_URL` + `AUTOGEN_OPENAI_API_KEY` explicitly
  (OpenRouter, Azure OpenAI, LiteLLM proxy, etc.).

Contracts:
- Must not log secrets.
- `allow_cloud_escalation: false` on the request forces local endpoint only (sovereignty).
"""

from __future__ import annotations

import os
from typing import Any

from shared_schemas.config import get_provider_settings

from rd_lab.throttle.routing_rules import is_cloud_escalation_allowed, is_cloud_first

# Gemini API (Google AI Studio) — OpenAI-compatible surface.
# https://ai.google.dev/gemini-api/docs/openai
DEFAULT_GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"


def should_use_remote_openai_compat(*, constraints: dict[str, Any]) -> bool:
    """
    Remote = any HTTPS OpenAI-compatible provider (Gemini, proxy, etc.), not loopback Ollama.
    """

    settings = get_provider_settings()
    if not is_cloud_escalation_allowed(constraints=constraints):
        return False
    if is_cloud_first(constraints=constraints):
        return True
    if settings.provider_mode in {"GEMINI", "ANTHROPIC"}:
        return True
    return False


def resolve_autogen_openai_config(
    *,
    model: str,
    temperature: float,
    constraints: dict[str, Any],
) -> dict[str, Any]:
    """
    Returns an AutoGen-style `llm_config` dict (`config_list`, `temperature`, `timeout`).
    """

    settings = get_provider_settings()
    remote = should_use_remote_openai_compat(constraints=constraints)

    override_base = (os.getenv("AUTOGEN_OPENAI_BASE_URL") or os.getenv("OPENAI_COMPAT_BASE_URL") or "").strip()
    override_key = (os.getenv("AUTOGEN_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()

    base_url: str
    api_key: str

    if override_base and override_key:
        base_url = override_base
        api_key = override_key
    elif not remote:
        base_url = settings.vllm_base_url
        api_key = os.getenv("AUTOGEN_OPENAI_API_KEY_LOCAL", "local")
    elif settings.provider_mode == "ANTHROPIC":
        base_url = (os.getenv("ANTHROPIC_OPENAI_COMPAT_BASE_URL") or "").strip()
        api_key = (override_key or settings.anthropic_api_key or "").strip()
        if not base_url:
            raise ValueError(
                "Anthropic has no native OpenAI-compatible endpoint in-process. "
                "Set AUTOGEN_OPENAI_BASE_URL + AUTOGEN_OPENAI_API_KEY to an OpenAI-compatible proxy "
                "(e.g. LiteLLM), or set ANTHROPIC_OPENAI_COMPAT_BASE_URL if you run such a proxy."
            )
    else:
        # Gemini (explicit cloud tier, PROVIDER_MODE=GEMINI, or default remote path)
        base_url = (os.getenv("GEMINI_OPENAI_BASE_URL") or DEFAULT_GEMINI_OPENAI_BASE_URL).strip()
        api_key = (settings.google_api_key or "").strip()
        if not api_key:
            raise ValueError(
                "Remote Gemini requires GOOGLE_API_KEY (or set AUTOGEN_OPENAI_API_KEY for a custom OpenAI-compatible URL)."
            )

    timeout_default = "120" if remote else "45"
    return {
        "config_list": [
            {
                "model": model,
                "base_url": base_url.rstrip("/"),
                "api_key": api_key,
            }
        ],
        "temperature": float(temperature),
        "timeout": int(os.getenv("AUTOGEN_REQUEST_TIMEOUT_SECONDS", timeout_default)),
    }
