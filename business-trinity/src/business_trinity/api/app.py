"""
Rationale: Provide a minimal HTTP surface for Trinity integration.

How:
- Exposes `GET /health` so operators can verify the container is running.

Contracts:
- In the future, additional endpoints will accept incoming triggers and
  create work orders for n8n.
- This scaffolding does not execute external side effects directly.
"""

from fastapi import FastAPI

app = FastAPI(title="Trinity API (Sovereign AI OS)")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

