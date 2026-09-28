from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.locations.errors import DeviceNotFoundError, ZoneNotFoundError
from src.infrastructure.persistence.models import DeviceRow, ZoneRow


def _device_dict(d: DeviceRow) -> dict:
    return {
        "id": d.id,
        "device_type": d.device_type,
        "role": d.role,
        "display_name": d.display_name,
        "device_family": d.device_family,
        "zone_id": d.zone_id,
        "location_id": d.location_id,
    }


class DeviceZoneRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def assign(self, device_id: UUID, zone_id: Optional[UUID]) -> dict:
        """Sets zone_id and location_id (copied from the zone) in one write;
        clears both when zone_id is None."""
        try:
            device = self._session.get(DeviceRow, device_id)
            if device is None:
                raise DeviceNotFoundError(f"device {device_id} not found")
            if zone_id is None:
                device.zone_id = None
                device.location_id = None
            else:
                zone = self._session.get(ZoneRow, zone_id)
                if zone is None:
                    raise ZoneNotFoundError(f"zone {zone_id} not found")
                device.zone_id = zone.id
                device.location_id = zone.location_id
            self._session.commit()
            self._session.refresh(device)
            return _device_dict(device)
        except Exception:
            self._session.rollback()
            raise

    def list_by_zone(self, zone_id: UUID) -> list[dict]:
        rows = self._session.scalars(
            select(DeviceRow)
            .where(DeviceRow.zone_id == zone_id)
            .order_by(DeviceRow.created_at)
        ).all()
        return [_device_dict(r) for r in rows]