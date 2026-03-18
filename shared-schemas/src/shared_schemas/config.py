"""
Rationale: Provider selection and fallback must be defined once for both
hemispheres to preserve sovereignty and schema compatibility.

How:
- Reads configuration from `.env`.
- Exposes a typed provider settings object (`ProviderSettings`).
- Provides a fallback policy for local validation failures.

Contracts:
- `PROVIDER_MODE` in `{LOCAL, GEMINI, ANTHROPIC}`
- If `PROVIDER_MODE=LOCAL`, local base url must be
  `http://vllm-server:8000/v1`
- `FALLBACK_PROVIDER_MODE` defines the cloud provider for escalation.
- Fallback policy is triggered when local Pydantic validation fails 3
  times (orchestrator responsibility), and config provides the decision rule
  and cloud model construction helpers.
"""

from __future__ import annotations

import os
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


load_dotenv()  # Rationale: Load host-provided `.env` so containers behave
# consistently in air-gapped setups. How: Called at import-time for
# predictable settings resolution.

ProviderMode = Literal["LOCAL", "GEMINI", "ANTHROPIC"]


class ProviderSettings(BaseModel):
    """
    Rationale: Strong typing prevents provider-mode drift.

    How:
    - Validates environment variables and defines the fallback target.
    """

    provider_mode: ProviderMode = Field(default="LOCAL")
    fallback_provider_mode: ProviderMode = Field(default="GEMINI")

    # Required by your spec.
    vllm_base_url: str = Field(default="http://vllm-server:8000/v1")

    # Optional model name knobs; can be wired later.
    model_name: Optional[str] = None

    # Provider keys (only used when that provider mode is active).
    google_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)

    @field_validator("fallback_provider_mode")
    @classmethod
    def _validate_fallback_cloud_only(cls, v: ProviderMode) -> ProviderMode:
        # Rationale: Escalation should go from LOCAL -> cloud.
        # How: Allow GEMINI/ANTHROPIC only; LOCAL fallback would be redundant.
        if v == "LOCAL":
            raise ValueError("FALLBACK_PROVIDER_MODE must not be LOCAL.")
        return v


class ValidationFallbackPolicy(BaseModel):
    """
    Rationale: Encodes the escalation trigger rule once.

    How:
    - If local output fails Pydantic validation repeatedly, we escalate.
    """

    max_validation_failures: int = Field(default=3, ge=1)

    def should_escalate(self, validation_failures: int) -> bool:
        """
        Rationale: Deterministic escalation behavior.

        Contracts:
        - `validation_failures` counts consecutive local Pydantic failures.
        """

        return validation_failures >= self.max_validation_failures


_DEFAULT_POLICY = ValidationFallbackPolicy()


def get_provider_settings() -> ProviderSettings:
    """
    Rationale: One canonical settings loader.

    How:
    - Reads env vars with defaults aligned to the architecture spec.
    """

    return ProviderSettings(
        provider_mode=os.getenv("PROVIDER_MODE", "LOCAL"),
        fallback_provider_mode=os.getenv("FALLBACK_PROVIDER_MODE", "GEMINI"),
        vllm_base_url=os.getenv("VLLM_BASE_URL", "http://vllm-server:8000/v1"),
        model_name=os.getenv("MODEL_NAME"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )


def get_validation_fallback_policy() -> ValidationFallbackPolicy:
    """
    Rationale: Provide the standardized escalation trigger.

    Contracts:
    - Default is 3 local failures -> escalate.
    """

    return _DEFAULT_POLICY


def should_escalate_local(validation_failures: int) -> bool:
    """
    Rationale: Orchestrator uses this decision rule.

    How:
    - Delegates to the policy object.
    """

    return _DEFAULT_POLICY.should_escalate(validation_failures)


def build_llm(settings: ProviderSettings):
    """
    Rationale: Lazily construct the active LLM client for the hemisphere.

    How:
    - Imports LangChain providers only at runtime to keep shared schemas light.

    Contracts:
    - For scaffolding, if LangChain connector packages are missing, this
      function raises a descriptive ImportError.
    """

    if settings.provider_mode == "LOCAL":
        from langchain_openai import ChatOpenAI

        # Rationale: vLLM exposes an OpenAI-compatible REST API.
        return ChatOpenAI(
            base_url=settings.vllm_base_url,
            api_key="local",
            model=settings.model_name or "local-model",
        )

    if settings.provider_mode == "GEMINI":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            api_key=settings.google_api_key,
            model=settings.model_name or "gemini-pro",
        )

    if settings.provider_mode == "ANTHROPIC":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model=settings.model_name or "claude-3-5-sonnet",
        )

    raise ValueError(f"Unsupported provider mode: {settings.provider_mode}")


def build_cloud_llm_for_escalation(
    settings: ProviderSettings, *, cloud_provider_mode: ProviderMode
):
    """
    Rationale: Escalate to a cloud provider for a specific task.

    How:
    - Builds a model client for the chosen cloud provider, without changing
      how records are validated/serialized.
    """

    cloud_settings = settings.model_copy(update={"provider_mode": cloud_provider_mode})
    return build_llm(cloud_settings)

