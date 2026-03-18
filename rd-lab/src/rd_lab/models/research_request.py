"""
Rationale: RD Lab consumes schema-validated requests from `spinalcord/requests`.

How:
- Defines the minimal request shape needed for AutoGen to generate a
  `ResearchDiscovery`.

Contracts:
- Required `rationale` must be written to local Rhythms before any LLM debate.
- Contains no secrets; only safe, auditable fields.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from shared_schemas.versioning import SchemaVersion, validate_semver


class ResearchRequest(BaseModel):
    """
    Rationale: Input schema prevents ambiguous prompts and improves
    deterministic validation/retry behavior.

    How:
    - Trinity writes these JSON files to `spinalcord/requests/*.json`.
    - RD Lab validates them and uses the prompt fields to drive AutoGen.
    """

    request_id: UUID = Field(default_factory=uuid4)
    schema_version: SchemaVersion = Field(default="0.1.0")
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    correlation_id: UUID
    research_question: str = Field(min_length=1)
    rationale: str = Field(min_length=1)

    # Optional constraints to guide the debate (e.g. "prefer citations", "no code").
    constraints: dict[str, Any] = Field(default_factory=dict)

    # Optionally link the upstream DecisionRecord (future improvement).
    linked_decision_record_id: Optional[UUID] = None

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, v: SchemaVersion) -> SchemaVersion:
        validate_semver(str(v))
        return v

