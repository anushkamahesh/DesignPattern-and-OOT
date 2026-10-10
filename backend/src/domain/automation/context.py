from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class LocationAutomationContext:
    """Plain data a strategy decides from: one zone's thresholds plus the
    latest readings among sensors assigned to that zone. No ORM rows."""

    location_id: UUID
    zone_id: UUID
    zone_low: float
    zone_high: float
    latest_moisture: Optional[float] = None  # None = no moisture reading in this zone
    latest_light: Optional[float] = None