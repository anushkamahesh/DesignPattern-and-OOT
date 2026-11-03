from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class OverviewLocation(BaseModel):
    id: UUID
    name: str


class OverviewDeviceCounts(BaseModel):
    sensor: int
    actuator: int


class OverviewDevice(BaseModel):
    id: UUID
    device_type: str
    role: str
    display_name: Optional[str] = None


class OverviewReading(BaseModel):
    device_id: UUID
    value: float
    unit: str
    recorded_at: datetime
    tracking_enabled: bool
    sampling_interval_seconds: int


class OverviewZone(BaseModel):
    id: UUID
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    devices: list[OverviewDevice]
    latest_readings: list[OverviewReading]


class OverviewRecommendation(BaseModel):
    action: str
    reason: str


class LocationOverviewDto(BaseModel):
    location: OverviewLocation
    device_counts: OverviewDeviceCounts
    zones: list[OverviewZone]
    strategy_key: Optional[str] = None
    last_recommendation: Optional[OverviewRecommendation] = None