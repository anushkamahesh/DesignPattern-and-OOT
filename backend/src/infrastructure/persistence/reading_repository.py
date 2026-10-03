from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.sensors.reading import Reading
from src.infrastructure.persistence.models import DeviceRow, ReadingRow


class ReadingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_device(self, device_id: UUID) -> Optional[DeviceRow]:
        return self._session.get(DeviceRow, device_id)

    def insert(self, reading: Reading) -> ReadingRow:
        row = ReadingRow(
            device_id=reading.device_id,
            value=reading.value,
            unit=reading.unit,
            source=reading.source,
            recorded_at=reading.recorded_at,
        )
        try:
            self._session.add(row)
            self._session.commit()
            self._session.refresh(row)
        except Exception:
            self._session.rollback()
            raise
        return row

    def list_recent(self, device_id: UUID, limit: int = 50) -> Sequence[ReadingRow]:
        return self._session.scalars(
            select(ReadingRow)
            .where(ReadingRow.device_id == device_id)
            .order_by(ReadingRow.recorded_at.desc())
            .limit(limit)
        ).all()

    def get_latest(self, device_id: UUID) -> Optional[ReadingRow]:
        return self._session.scalars(
            select(ReadingRow)
            .where(ReadingRow.device_id == device_id)
            .order_by(ReadingRow.recorded_at.desc())
            .limit(1)
        ).first()

    def list_simulation_tracked_devices(self) -> Sequence[DeviceRow]:
        """Tracking-enabled devices; the sampler filters protocol == simulation
        itself, since that lives in the default_config JSON."""
        return self._session.scalars(
            select(DeviceRow).where(DeviceRow.tracking_enabled.is_(True))
        ).all()