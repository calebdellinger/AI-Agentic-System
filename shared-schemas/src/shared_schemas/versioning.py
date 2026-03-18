"""
Rationale: Versioning prevents silent schema drift between hemispheres.

How:
- Defines a lightweight `SchemaVersion` type and helper validators.

Contracts:
- Used by record models (`DecisionRecord`, `ResearchDiscovery`, etc.).
"""

from __future__ import annotations

from typing import NewType


# Rationale: Represent versions as plain strings while validating format.
# How: Pydantic models validate the format via `validate_semver()`.
SchemaVersion = NewType("SchemaVersion", str)


def validate_semver(version: str) -> None:
    """
    Rationale: Enforce a consistent semantic version string format.

    How: Basic validation only; full compatibility rules live elsewhere.

    Contracts:
    - Input: `version` like `0.1.0`
    - Raises: `ValueError` if invalid.
    """
    import re

    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"Invalid semver version: {version!r}")


SUPPORTED_SCHEMA_VERSION = "0.1.0"

