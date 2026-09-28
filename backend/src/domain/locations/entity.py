from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class Zone:
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: dict = field(default_factory=dict)
    id: Optional[UUID] = None


@dataclass(frozen=True)
class Location:
    name: str
    zones: tuple[Zone, ...] = field(default_factory=tuple)
    id: Optional[UUID] = None


@dataclass(frozen=True)
class LocationConfig:
    location: Location