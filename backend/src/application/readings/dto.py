from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReadingDto(BaseModel):
    device_id: UUID
    value: float
    unit: str
    source: str
    recorded_at: datetime


class SamplingUpdateRequest(BaseModel):
    sampling_interval_seconds: int
    tracking_enabled: bool


class SamplingResponse(BaseModel):
    id: UUID
    sampling_interval_seconds: int
    tracking_enabled: bool