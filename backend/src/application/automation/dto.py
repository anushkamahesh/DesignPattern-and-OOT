from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class StrategySaveRequest(BaseModel):
    strategy_key: str


class AutomationRuleResponse(BaseModel):
    location_id: UUID
    strategy_key: Optional[str] = None


class ZoneRecommendationResponse(BaseModel):
    zone_id: UUID
    zone_name: str
    latest_moisture: Optional[float] = None
    action: str
    reason: str
    score: Optional[float] = None


class EvaluationResponse(BaseModel):
    location_id: UUID
    strategy_key: str
    recommendations: list[ZoneRecommendationResponse]