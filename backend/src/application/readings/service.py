from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from src.application.readings.dto import ReadingDto
from src.domain.sensors.reading import Reading
from src.infrastructure.adapters.sensors.selector import select_sensor_adapter
from src.infrastructure.persistence.reading_repository import ReadingRepository


class DeviceNotFoundError(LookupError):
    """The requested device does not exist."""


class AdapterError(ValueError):
    """The adapter could not produce a reading for this device."""


def _to_dto(row) -> ReadingDto:
    return ReadingDto(
        device_id=row.device_id,
        value=float(row.value),
        unit=row.unit,
        source=row.source,
        recorded_at=row.recorded_at,
    )


class ReadingIngest:
    """The only writer of sensor_readings."""

    def __init__(self, repo: ReadingRepository) -> None:
        self._repo = repo

    def record_read(self, device_id: UUID, now: datetime | None = None) -> ReadingDto:
        now = now or datetime.now(timezone.utc)
        device = self._repo.get_device(device_id)
        if device is None:
            raise DeviceNotFoundError(str(device_id))
        try:
            adapter = select_sensor_adapter(device.default_config or {})
            reading = adapter.read(
                device.id, device.device_type, device.default_config or {}, now
            )
        except ValueError as exc:
            raise AdapterError(str(exc)) from exc
        row = self._repo.insert(reading)
        return _to_dto(row)

    def record_translated(self, reading: Reading) -> ReadingDto:
        """Persists an already-translated reading, e.g. from the MQTT
        adapter's translate() output. Phase 12's subscriber calls this."""
        row = self._repo.insert(reading)
        return _to_dto(row)

    def list_recent(self, device_id: UUID, limit: int = 50) -> list[ReadingDto]:
        return [_to_dto(r) for r in self._repo.list_recent(device_id, limit)]

    def latest(self, device_id: UUID) -> ReadingDto | None:
        row = self._repo.get_latest(device_id)
        return _to_dto(row) if row else None