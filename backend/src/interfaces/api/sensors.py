from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.application.readings.dto import ReadingDto
from src.application.readings.service import AdapterError, DeviceNotFoundError, ReadingIngest
from src.application.sensors.service import SensorService
from src.infrastructure.persistence.device_repository import DeviceRepository
from src.infrastructure.persistence.reading_repository import ReadingRepository
from src.infrastructure.persistence.session import get_db

router = APIRouter(
    prefix="/api/sensors",
    tags=["sensors"],
)


class CreateSensorRequest(BaseModel):
    type: str
    display_name: str | None = None


class SensorResponse(BaseModel):
    id: UUID
    device_type: str
    display_name: str
    default_config: dict


def get_sensor_service(db: Session = Depends(get_db)) -> SensorService:
    return SensorService(DeviceRepository(db))


def get_reading_ingest(db: Session = Depends(get_db)) -> ReadingIngest:
    return ReadingIngest(ReadingRepository(db))


@router.get("", response_model=list[SensorResponse])
def list_sensors(
    service: SensorService = Depends(get_sensor_service),
):
    return service.list_sensors()


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sensor(
    request: CreateSensorRequest,
    service: SensorService = Depends(get_sensor_service),
):
    try:
        return service.create_sensor(
            sensor_type=request.type,
            display_name=request.display_name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{device_id}/read",
    response_model=ReadingDto,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger a one-shot read through the device's adapter",
)
def read_sensor(
    device_id: UUID,
    ingest: ReadingIngest = Depends(get_reading_ingest),
):
    try:
        return ingest.record_read(device_id)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AdapterError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/{device_id}/readings",
    response_model=list[ReadingDto],
    summary="List recent readings for a device, newest first",
)
def list_readings(
    device_id: UUID,
    limit: int = Query(default=50, ge=1, le=500),
    ingest: ReadingIngest = Depends(get_reading_ingest),
):
    return ingest.list_recent(device_id, limit=limit)