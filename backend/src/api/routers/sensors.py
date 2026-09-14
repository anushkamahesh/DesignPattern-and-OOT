from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..schemas import SensorCreateRequest, SensorResponse
from ..dependencies import get_db
from ...application.services.sensor_service import SensorService


router = APIRouter(prefix="/api/sensors", tags=["sensors"])


@router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(
    payload: SensorCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        service = SensorService(db)
        return service.create_sensor(
            sensor_type=payload.sensor_type,
            display_name=payload.display_name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=list[SensorResponse])
def list_sensors(
    db: Session = Depends(get_db),
):
    service = SensorService(db)
    return service.list_sensors()
