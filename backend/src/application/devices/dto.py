from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ActuatorDto(BaseModel):
    id: UUID
    device_type: str
    role: str
    display_name: Optional[str] = None
    device_family: str
    zone_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    state: str
    allowed_commands: list[str]
    allowed_targets: list[str]


class TransitionRequest(BaseModel):
    target: str