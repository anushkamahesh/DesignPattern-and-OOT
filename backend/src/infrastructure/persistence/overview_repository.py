from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import DeviceRow, ReadingRow


@dataclass(frozen=True)
class AssignedDevice:
    id: UUID
    zone_id: UUID
    device_type: str
    role: str
    display_name: Optional[str]
    tracking_enabled: bool
    sampling_interval_seconds: int


@dataclass(frozen=True)
class LatestReading:
    device_id: UUID
    value: float
    unit: str
    recorded_at: datetime


class OverviewRepository:
    """Read-only queries for the location overview."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_assigned_devices(self, location_id: UUID) -> list[AssignedDevice]:
        """One query: devices with this location_id and a non-null zone_id.
        Unassigned devices are never returned."""
        rows = self._session.scalars(
            select(DeviceRow)
            .where(DeviceRow.location_id == location_id, DeviceRow.zone_id.is_not(None))
            .order_by(DeviceRow.created_at, DeviceRow.id)
        ).all()
        return [
            AssignedDevice(
                id=r.id,
                zone_id=r.zone_id,
                device_type=r.device_type,
                role=r.role,
                display_name=r.display_name,
                tracking_enabled=r.tracking_enabled,
                sampling_interval_seconds=r.sampling_interval_seconds,
            )
            for r in rows
        ]

    def latest_readings(self, device_ids: Sequence[UUID]) -> list[LatestReading]:
        """One query for all devices: the newest row per device (Postgres
        DISTINCT ON), using the (device_id, recorded_at) index. A device with no
        row is simply absent. Readings are not filtered by source."""
        if not device_ids:
            return []
        rows = self._session.scalars(
            select(ReadingRow)
            .where(ReadingRow.device_id.in_(list(device_ids)))
            .distinct(ReadingRow.device_id)
            .order_by(ReadingRow.device_id, ReadingRow.recorded_at.desc())
        ).all()
        return [
            LatestReading(
                device_id=r.device_id,
                value=float(r.value),
                unit=r.unit,
                recorded_at=r.recorded_at,
            )
            for r in rows
        ]