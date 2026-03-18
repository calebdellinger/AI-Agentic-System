"""
Rationale: Your spec requests `config.py` under `/shared`.

How:
- This module re-exports the canonical implementation from
  `shared_schemas.config` so both hemispheres can use a consistent provider
  and fallback contract.

Contracts:
- Reading from `.env` is handled inside `shared_schemas.config`.
"""

from __future__ import annotations

from shared_schemas.config import (  # noqa: F401
    ProviderMode,
    ProviderSettings,
    get_provider_settings,
    get_validation_fallback_policy,
    should_escalate_local,
)

__all__ = [
    "ProviderMode",
    "ProviderSettings",
    "get_provider_settings",
    "get_validation_fallback_policy",
    "should_escalate_local",
]

