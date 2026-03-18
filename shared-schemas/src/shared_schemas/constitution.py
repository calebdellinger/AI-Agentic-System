"""
Rationale: Constitutional logic provides evidence-based guardrails.

How:
- Defines minimal scaffold types used to represent check results.
- Does not bind to any specific agentic framework.

Contracts:
- Used by hemispheres to record validation outcomes in DecisionRecords.
"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ConstitutionCheckResult(BaseModel):
    """
    Rationale: Keep "passed/failed + evidence" consistent across modules.

    How: Captures rule id, pass status, and a small evidence summary.
    """

    rule_id: str = Field(min_length=1)
    passed: bool
    evidence_summary: str = Field(min_length=1)


ConstitutionStatus = Literal["pass", "fail"]

