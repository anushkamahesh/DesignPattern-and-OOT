from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.application.devices.dto import ActuatorDto, TransitionRequest
from src.application.devices.service import ActuatorNotFoundError, ActuatorStateService
from src.domain.actuators.state import IllegalTransitionError, UnknownStateError
from src.infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from src.infrastructure.persistence.session import get_db

router = APIRouter(prefix="/api", tags=["Actuators"])


def get_service(db: Session = Depends(get_db)) -> ActuatorStateService:
    return ActuatorStateService(ActuatorStateRepository(db))


@router.get(
    "/actuators",
    response_model=list[ActuatorDto],
    summary="List actuators with their state and allowed commands",
)
def list_actuators(service: ActuatorStateService = Depends(get_service)):
    return service.list_actuators()


@router.get(
    "/actuators/{device_id}",
    response_model=ActuatorDto,
    summary="One actuator with its state and allowed commands",
)
def get_actuator(device_id: UUID, service: ActuatorStateService = Depends(get_service)):
    try:
        return service.get_actuator(device_id)
    except ActuatorNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/devices/{device_id}/transition",
    response_model=ActuatorDto,
    summary="Move an actuator to a target state (409 if the transition is illegal)",
)
def transition(
    device_id: UUID,
    req: TransitionRequest,
    service: ActuatorStateService = Depends(get_service),
):
    try:
        return service.transition(device_id, req.target)
    except ActuatorNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except IllegalTransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except UnknownStateError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc