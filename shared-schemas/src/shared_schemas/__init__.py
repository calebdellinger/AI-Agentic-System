"""
Rationale: `shared_schemas` is the only cross-hemisphere bridge.

How:
- Exposes the initial schema types and configuration contract used by
  `business-trinity` and `rd-lab`.

Contracts:
- Code in hemispheres should import schema types from here to ensure
  consistent validation and "Decision DNA" preservation via required
  `rationale` fields.
"""

from .config import ProviderMode, ProviderSettings, get_provider_settings
from .constitution import ConstitutionCheckResult
from .decision_record import DecisionRecord
from .research_discovery import ResearchDiscovery
from .rhythm_event import RhythmEvent
from .versioning import SchemaVersion
from .work_order import WorkOrder

__all__ = [
    "ProviderMode",
    "ProviderSettings",
    "get_provider_settings",
    "ConstitutionCheckResult",
    "DecisionRecord",
    "ResearchDiscovery",
    "RhythmEvent",
    "SchemaVersion",
    "WorkOrder",
]

