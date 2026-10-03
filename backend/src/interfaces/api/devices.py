from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.application.readings.dto import SamplingResponse, SamplingUpdateRequest
from src.infrastructure.persistence.models import DeviceRow
from src.infrastructure.persistence.session import get_db

router = APIRouter(prefix="/api/devices", tags=["devices"])

MIN_INTERVAL_SECONDS = 5


@router.patch(
    "/{device_id}/sampling",
    response_model=SamplingResponse,
    summary="Update a device's sampling interval and tracking flag",
)
def update_sampling(device_id: UUID, req: SamplingUpdateRequest, db: Session = Depends(get_db)):
    if req.sampling_interval_seconds < MIN_INTERVAL_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"sampling_interval_seconds must be at least {MIN_INTERVAL_SECONDS}",
        )
    device = db.get(DeviceRow, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="device not found")
    try:
        device.sampling_interval_seconds = req.sampling_interval_seconds
        device.tracking_enabled = req.tracking_enabled
        db.commit()
        db.refresh(device)
    except Exception:
        db.rollback()
        raise
    return SamplingResponse(
        id=device.id,
        sampling_interval_seconds=device.sampling_interval_seconds,
        tracking_enabled=device.tracking_enabled,
    )