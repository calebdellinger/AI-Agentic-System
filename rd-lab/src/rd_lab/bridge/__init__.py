"""
Rationale: Bridge implements file-based exchange contracts.

How:
- Inbox reads requests from `spinalcord/requests`.
- Outbox writes discoveries and decision records to `spinalcord/discoveries`.
- Debate transcript streams AutoGen turns to `spinalcord/debates` for the UI.
"""

