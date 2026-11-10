from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


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


class ApplyRequest(BaseModel):
    command: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ExecutionDto(BaseModel):
    id: UUID
    device_id: UUID
    success: bool
    policy_applied: list[str]
    message: Optional[str] = None
    created_at: datetime