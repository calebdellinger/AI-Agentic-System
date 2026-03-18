"""
Rationale: DinD sandbox runner enforces Lab air-gap at runtime.

How (scaffolding stage):
- Defines the interface for running inner workloads with no-network.

Contracts:
- Must prevent inner containers from accessing the public internet.
- Implementation will use Docker network controls such as `--network none`
  or an internal-only network.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class SandboxRunRequest:
    """
    Rationale: Make sandbox intent explicit for auditing.

    Contracts:
    - `command` describes the inner workload.
    - `inputs` must not contain secrets that cannot be logged safely.
    """

    command: str
    inputs: dict[str, Any]
    timeout_seconds: Optional[int] = None


def run_in_dind_sandbox_no_network(request: SandboxRunRequest) -> dict[str, Any]:
    """
    Rationale: Only innovation code runs in a locked sandbox.

    How:
    - Placeholder for Phase 3 DinD implementation.

    Contracts:
    - Must return a dict of structured results without exposing secrets.
    """

    # Rationale: Scaffolding doesn't execute inner containers yet.
    # How: Implementation will enforce `--network none`.
    return {"ok": False, "reason": "scaffold_only"}

