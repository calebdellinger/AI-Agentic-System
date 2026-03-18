"""
Rationale: Trinity converts internal discoveries into n8n WorkOrder intents.

How:
- Defines scaffolding to POST a schema-validated `WorkOrder` to n8n.

Contracts:
- Trinity should not execute external side effects directly.
- This module is responsible for outbound POSTing to n8n only.
"""

from __future__ import annotations

from typing import Any, Optional

import requests

from shared_schemas.work_order import WorkOrder


def post_work_order_to_n8n(
    *,
    work_order: WorkOrder,
    webhook_url: str,
    webhook_secret: Optional[str] = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    """
    Rationale: Keep external action dispatch behind a single function.

    How:
    - Sends `work_order.model_dump()` to the n8n webhook.
    - Optional `webhook_secret` will be used later for signature verification.

    Contracts:
    - Payload must remain free of secrets.
    - Must include `idempotency_key` for safe retries.
    """

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if webhook_secret:
        headers["X-WorkOrder-Secret"] = webhook_secret

    response = requests.post(
        webhook_url,
        headers=headers,
        json=work_order.model_dump(),
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    # n8n can respond with structured JSON later.
    return {"ok": True, "status_code": response.status_code}

