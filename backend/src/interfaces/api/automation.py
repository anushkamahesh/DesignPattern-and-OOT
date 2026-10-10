from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.application.automation.dto import (
    AutomationRuleResponse,
    EvaluationResponse,
    StrategySaveRequest,
)
from src.application.automation.service import AutomationService, StrategyNotSetError
from src.domain.automation.strategy import UnknownStrategyError
from src.domain.locations.errors import LocationNotFoundError
from src.infrastructure.persistence.automation_repository import AutomationRepository
from src.infrastructure.persistence.location_repository import LocationRepository
from src.infrastructure.persistence.session import get_db

router = APIRouter(prefix="/api", tags=["Automation"])


def get_automation_service(db: Session = Depends(get_db)) -> AutomationService:
    return AutomationService(LocationRepository(db), AutomationRepository(db))


@router.get(
    "/automation/strategies",
    response_model=list[str],
    summary="List the known strategy keys",
)
def list_strategies(service: AutomationService = Depends(get_automation_service)):
    return service.list_strategies()


@router.get(
    "/locations/{location_id}/automation",
    response_model=AutomationRuleResponse,
    summary="Get the saved strategy for a location (null if none)",
)
def get_rule(location_id: UUID, service: AutomationService = Depends(get_automation_service)):
    try:
        return service.get_rule(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put(
    "/locations/{location_id}/automation",
    response_model=AutomationRuleResponse,
    summary="Save (upsert) the active strategy for a location",
)
def save_rule(
    location_id: UUID,
    req: StrategySaveRequest,
    service: AutomationService = Depends(get_automation_service),
):
    try:
        return service.save_rule(location_id, req.strategy_key)
    except LocationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnknownStrategyError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/locations/{location_id}/automation/evaluate",
    response_model=EvaluationResponse,
    summary="Evaluate every zone with the location's saved strategy",
)
def evaluate(location_id: UUID, service: AutomationService = Depends(get_automation_service)):
    try:
        return service.evaluate(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (StrategyNotSetError, UnknownStrategyError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc