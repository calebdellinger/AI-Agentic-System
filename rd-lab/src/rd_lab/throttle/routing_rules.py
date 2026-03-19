"""
Rationale: Throttle/routing rules decide which local model size to use
per request attempt to optimize cost vs. schema correctness.

This is intentionally heuristic-only (no extra LLM calls) so it remains
deterministic and cheap. In a future iteration, you can replace/augment
these heuristics with learned metrics or token-count estimates.
"""

from __future__ import annotations

import os
from typing import Any


HEAVY_KEYWORDS = [
    # Formal reasoning / math
    "proof",
    "theorem",
    "lemma",
    "integral",
    "differential",
    "derivative",
    "equation",
    "inequality",
    "optimization",
    "complexity",
    "crypt",
    "cryptography",
    "formal",
    "rigorous",
    # Engineering/programming heavy
    "algorithm",
    "pseudocode",
    "implementation",
    "code",
    "debug",
    "benchmark",
    "experiment",
    "evaluate",
    "simulation",
    "modeling",
    # Multi-step / long instructions
    "multi-step",
    "step-by-step",
    "long",
    "detailed",
    "thorough",
    "compare",
    "tradeoff",
]


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def compute_initial_tier(*, research_question: str, constraints: dict[str, Any]) -> str:
    """
    Returns "light" or "heavy".

    Priority order:
    1) Explicit request constraint: `constraints.compute_tier`
    2) Heuristic classification based on question text
    """

    explicit = constraints.get("compute_tier")
    if isinstance(explicit, str):
        explicit_norm = explicit.strip().lower()
        if explicit_norm in {"light", "heavy"}:
            return explicit_norm
        # "auto" (or anything else) means defer to heuristics.
        if explicit_norm in {"auto", ""}:
            pass

    q = _norm(research_question)
    if not q:
        return "light"

    # Length heuristic: long questions often require better instruction-following
    # and more structured synthesis.
    if len(q) >= int(os.getenv("THROTTLE_HEAVY_MIN_CHARS", "260")):
        return "heavy"

    for kw in HEAVY_KEYWORDS:
        if kw in q:
            return "heavy"

    return "light"


def should_upgrade_to_heavy(*, initial_tier: str, attempt: int) -> bool:
    """
    Upgrade policy:
    - If request is initially classified as heavy, always use heavy.
    - Otherwise start on light, then upgrade after a small number of failures.

    `LOCAL_MAX_LIGHT_ATTEMPTS` defaults to 1 meaning:
      attempt=1 -> light
      attempt>=2 -> heavy
    """

    if initial_tier == "heavy":
        return True

    max_light_attempts = int(os.getenv("LOCAL_MAX_LIGHT_ATTEMPTS", "1"))
    return attempt > max_light_attempts

