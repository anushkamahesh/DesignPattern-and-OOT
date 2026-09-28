from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ZoneCreateRequest(BaseModel):
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: dict[str, Any] = Field(default_factory=dict)


class LocationConfigCreateRequest(BaseModel):
    location_name: str
    zones: list[ZoneCreateRequest]


class ZoneUpdateRequest(BaseModel):
    name: Optional[str] = None
    moisture_threshold_low: Optional[float] = None
    moisture_threshold_high: Optional[float] = None
    schedule: Optional[dict[str, Any]] = None


class LocationSummaryResponse(BaseModel):
    id: UUID
    name: str


class ZoneResponse(BaseModel):
    id: UUID
    location_id: UUID
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: dict[str, Any]


class LocationConfigResponse(BaseModel):
    location: LocationSummaryResponse
    zones: list[ZoneResponse]


class DeviceZoneAssignRequest(BaseModel):
    zone_id: Optional[UUID] = None

class DeviceZoneResponse(BaseModel):
    id: UUID
    zone_id: Optional[UUID] = None
    location_id: Optional[UUID] = None


class ZoneDeviceResponse(BaseModel):
    id: UUID
    device_type: str
    role: str
    display_name: Optional[str] = None
    device_family: str
    zone_id: Optional[UUID] = None
    location_id: Optional[UUID] = None