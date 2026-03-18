"""
Rationale: `ResearchDiscovery` is the Lab hemisphere's schema-validated
output for Trinity to execute.

How:
- Defines a strict Pydantic model that includes hypotheses, findings, and
  required `rationale`.

Contracts:
- Required field: `rationale`
- Does not carry raw tool output logs across hemispheres.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from .versioning import SchemaVersion, validate_semver


class Finding(BaseModel):
    """
    Rationale: Makes evidence structure stable across framework swaps.

    How: Represents a single claim plus supporting summary and confidence.
    """

    claim: str
    support_summary: str
    confidence: float = Field(ge=0.0, le=1.0)


class ResearchDiscovery(BaseModel):
    """
    Rationale: Provides the schema-validated "next steps" from R&D.

    How:
    - Lab emits this artifact into the `spinalcord` volume.
    - Trinity consumes it and turns it into execution tasks.

    Contracts:
    - `rationale` is required and non-empty.
    - `schema_version` format is validated.
    """

    discovery_id: UUID = Field(default_factory=uuid4)
    schema_version: SchemaVersion = Field(default="0.1.0")
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: UUID

    hypothesis: str
    methods: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    next_questions: list[str] = Field(default_factory=list)

    rationale: str = Field(min_length=1)
    linked_decision_record_id: Optional[UUID] = None

    # Ref pointers to local volume artifacts (no raw data or secrets).
    artifact_refs: list[dict[str, str]] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, v: SchemaVersion) -> SchemaVersion:
        validate_semver(str(v))
        return v

