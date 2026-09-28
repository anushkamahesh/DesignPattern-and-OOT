from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.application.locations.config_service import LocationConfigService
from src.application.locations.dto import (
    DeviceZoneAssignRequest,
    DeviceZoneResponse,
    LocationConfigCreateRequest,
    LocationConfigResponse,
    LocationSummaryResponse,
    ZoneCreateRequest,
    ZoneDeviceResponse,
    ZoneResponse,
    ZoneUpdateRequest,
)
from src.application.locations.zone_assignment_service import ZoneAssignmentService
from src.domain.locations.errors import (
    ConfigurationError,
    DeviceNotFoundError,
    LocationNotFoundError,
    ZoneNotFoundError,
)
from src.infrastructure.persistence.device_zone_repository import DeviceZoneRepository
from src.infrastructure.persistence.location_repository import LocationRepository
from src.infrastructure.persistence.session import get_db

router = APIRouter(prefix="/api", tags=["Locations & Zones"])


def get_config_service(db: Session = Depends(get_db)) -> LocationConfigService:
    return LocationConfigService(LocationRepository(db))


def get_assignment_service(db: Session = Depends(get_db)) -> ZoneAssignmentService:
    return ZoneAssignmentService(DeviceZoneRepository(db), LocationRepository(db))


def _http(exc: Exception) -> HTTPException:
    if isinstance(exc, ConfigurationError):
        return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))


_NOT_FOUND = (LocationNotFoundError, ZoneNotFoundError, DeviceNotFoundError)


# ---- locations ----
@router.post(
    "/locations/config",
    response_model=LocationConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a location with zones (Builder)",
)
def create_location_config(
    req: LocationConfigCreateRequest,
    service: LocationConfigService = Depends(get_config_service),
):
    try:
        return service.create_location_config(req)
    except ConfigurationError as exc:
        raise _http(exc) from exc


@router.get(
    "/locations",
    response_model=list[LocationSummaryResponse],
    summary="List locations (newest first)",
)
def list_locations(service: LocationConfigService = Depends(get_config_service)):
    return service.list_locations()


@router.get(
    "/locations/{location_id}/config",
    response_model=LocationConfigResponse,
    summary="Get a location with its zones",
)
def get_location_config(
    location_id: UUID, service: LocationConfigService = Depends(get_config_service)
):
    try:
        return service.get_location_config(location_id)
    except _NOT_FOUND as exc:
        raise _http(exc) from exc


@router.delete(
    "/locations/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a location and its zones",
)
def delete_location(
    location_id: UUID, service: LocationConfigService = Depends(get_config_service)
):
    try:
        service.delete_location(location_id)
    except _NOT_FOUND as exc:
        raise _http(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---- zones ----
@router.post(
    "/locations/{location_id}/zones",
    response_model=ZoneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a zone to a saved location",
)
def add_zone(
    location_id: UUID,
    req: ZoneCreateRequest,
    service: LocationConfigService = Depends(get_config_service),
):
    try:
        return service.add_zone(location_id, req)
    except (ConfigurationError, *_NOT_FOUND) as exc:
        raise _http(exc) from exc


@router.patch(
    "/locations/{location_id}/zones/{zone_id}",
    response_model=ZoneResponse,
    summary="Edit a zone's name, thresholds and schedule",
)
def update_zone(
    location_id: UUID,
    zone_id: UUID,
    req: ZoneUpdateRequest,
    service: LocationConfigService = Depends(get_config_service),
):
    try:
        return service.update_zone(location_id, zone_id, req)
    except (ConfigurationError, *_NOT_FOUND) as exc:
        raise _http(exc) from exc


@router.delete(
    "/locations/{location_id}/zones/{zone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a zone (not the last one); unassigns its devices",
)
def delete_zone(
    location_id: UUID,
    zone_id: UUID,
    service: LocationConfigService = Depends(get_config_service),
):
    try:
        service.delete_zone(location_id, zone_id)
    except (ConfigurationError, *_NOT_FOUND) as exc:
        raise _http(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---- assignment ----
@router.patch(
    "/devices/{device_id}/zone",
    response_model=DeviceZoneResponse,
    summary="Assign a device to a zone, or clear with zone_id null",
)
def assign_device_zone(
    device_id: UUID,
    req: DeviceZoneAssignRequest,
    service: ZoneAssignmentService = Depends(get_assignment_service),
):
    try:
        return service.assign_device_to_zone(device_id, req.zone_id)
    except _NOT_FOUND as exc:
        raise _http(exc) from exc


@router.get(
    "/locations/{location_id}/zones/{zone_id}/devices",
    response_model=list[ZoneDeviceResponse],
    summary="List devices assigned to a zone",
)
def list_zone_devices(
    location_id: UUID,
    zone_id: UUID,
    service: ZoneAssignmentService = Depends(get_assignment_service),
):
    try:
        return service.list_zone_devices(location_id, zone_id)
    except _NOT_FOUND as exc:
        raise _http(exc) from exc