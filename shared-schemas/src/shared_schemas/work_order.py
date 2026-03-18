"""
Rationale: `WorkOrder` is the bridge contract between Trinity and n8n.

How:
- Encodes "what to do externally" in a schema validated payload.
- Hemispheres never directly call external systems; n8n executes them.

Contracts:
- `idempotency_key` enables safe retries.
- `decision_dna_ref` links the work order back to a DecisionRecord.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


Operation = Literal["notion_create", "notion_update", "slack_post", "noop"]


class WorkOrder(BaseModel):
    """
    Rationale: Standardizes external side-effect instructions.

    How:
    - Trinity creates WorkOrder objects and posts them to n8n webhooks.

    Contracts:
    - `decision_dna_ref` must reference a `DecisionRecord.record_id`.
    - `idempotency_key` must be stable for retries.
    """

    work_order_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID
    operation: Operation

    # Typed payload by operation is intentionally relaxed at scaffolding time.
    # Implementation can introduce per-operation subclasses later.
    payload: dict[str, Any] = Field(default_factory=dict)

    decision_dna_ref: UUID
    idempotency_key: str = Field(min_length=1)

    created_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

