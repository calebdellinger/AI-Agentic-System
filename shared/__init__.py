"""
Rationale: Provide a stable import path for config outside of the schema
library.

How:
- Acts as a thin compatibility wrapper around `shared_schemas`.

Contracts:
- Keeps the architecture's "Spinal Cord bridge" as the source of truth.
"""

