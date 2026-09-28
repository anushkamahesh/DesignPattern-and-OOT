from typing import Optional
from uuid import UUID

from src.application.locations.dto import DeviceZoneResponse, ZoneDeviceResponse
from src.domain.locations.errors import ZoneNotFoundError


class ZoneAssignmentService:
    """Assign/unassign devices to zones on saved locations. Never uses the builder."""

    def __init__(self, device_repo, location_repo) -> None:
        self._devices = device_repo
        self._locations = location_repo

    def assign_device_to_zone(self, device_id: UUID, zone_id: Optional[UUID]) -> DeviceZoneResponse:
        return DeviceZoneResponse(**{
            k: v for k, v in self._devices.assign(device_id, zone_id).items()
            if k in ("id", "zone_id", "location_id")
        })

    def list_zone_devices(self, location_id: UUID, zone_id: UUID) -> list[ZoneDeviceResponse]:
        if self._locations.get_zone(location_id, zone_id) is None:
            raise ZoneNotFoundError(f"zone {zone_id} not found in location {location_id}")
        return [ZoneDeviceResponse(**d) for d in self._devices.list_by_zone(zone_id)]