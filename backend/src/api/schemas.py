from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from uuid import UUID


class SensorCreateRequest(BaseModel):
    sensor_type: str = Field(..., json_schema_extra={"example": "moisture"})
    display_name: Optional[str] = Field(None, json_schema_extra={"example": "Moisture Sensor"})


class SensorResponse(BaseModel):
    id: Optional[UUID]
    device_type: str
    display_name: Optional[str]
    default_config: Dict[str, Any]

    class Config:
        from_attributes = True
