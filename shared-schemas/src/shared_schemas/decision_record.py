"""
Rationale: `DecisionRecord` is the Decision DNA artifact.

How:
- Defines a strict Pydantic model used by both hemispheres to record why
  the system chose a plan/action.

Contracts:
- Required field: `rationale` (schema-agnostic "why")
- Immutable-ish metadata: record id, schema version, timestamp, correlation id
- Models should not contain raw tool secrets.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from .versioning import SchemaVersion, validate_semver


DecisionType = Literal["research", "execution", "tool_intent", "validation"]
DecisionStatus = Literal["pending", "completed", "failed"]
Hemisphere = Literal["trinity", "lab"]


class ArtifactRef(BaseModel):
    """
    Rationale: Avoids passing large or sensitive artifacts across hemispheres.

    How: Represents where a result lives in a mounted local volume.

    Contracts:
    - `volume_path` must be relative to the known mounted volume roots.
    """

    ref_id: str
    volume_path: str


class ConstitutionalCheck(BaseModel):
    """
    Rationale: Captures evidence-based validation results.

    How: Lists rule ids and summaries without importing framework-specific
    reasoning.
    """

    rule_id: str
    passed: bool
    evidence_summary: str


class DecisionRecord(BaseModel):
    """
    Rationale: Persist "why" for every orchestrator and lab decision.

    How:
    - Enforces required `rationale` to preserve Decision DNA.

    Contracts:
    - `rationale` is required and must be non-empty.
    - `schema_version` must match supported format.
    - `inputs_summary` and payload fields must not include secrets.
    """

    record_id: UUID = Field(default_factory=uuid4)
    schema_version: SchemaVersion = Field(default="0.1.0")
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    hemisphere: Hemisphere
    correlation_id: UUID

    decision_type: DecisionType
    rationale: str = Field(min_length=1)

    inputs_summary: dict[str, Any] = Field(default_factory=dict)
    decision_payload: dict[str, Any] = Field(default_factory=dict)
    outputs_summary: dict[str, Any] = Field(default_factory=dict)

    constitutional_checks: list[ConstitutionalCheck] = Field(default_factory=list)
    status: DecisionStatus = Field(default="pending")
    artifact_refs: list[ArtifactRef] = Field(default_factory=list)

    error: Optional[dict[str, Any]] = None

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, v: SchemaVersion) -> SchemaVersion:
        validate_semver(str(v))
        return v


