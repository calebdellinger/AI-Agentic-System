"""
Rationale: Contract tests ensure `rationale` remains required.

How:
- Creates a model with missing required fields and asserts validation fails.

Contracts:
- Pydantic must reject payloads without `rationale` in `DecisionRecord` and
  `ResearchDiscovery`.
"""

from uuid import uuid4

import pytest

from shared_schemas.decision_record import DecisionRecord
from shared_schemas.research_discovery import ResearchDiscovery


def test_decision_record_requires_rationale():
    with pytest.raises(Exception):
        DecisionRecord(
            hemisphere="trinity",
            correlation_id=uuid4(),
            decision_type="execution",
            # rationale missing
        )


def test_research_discovery_requires_rationale():
    with pytest.raises(Exception):
        ResearchDiscovery(
            correlation_id=uuid4(),
            hypothesis="test",
            # rationale missing
        )

