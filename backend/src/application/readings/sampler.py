from __future__ import annotations

from datetime import datetime, timezone

from src.application.readings.service import ReadingIngest
from src.infrastructure.persistence.reading_repository import ReadingRepository


class SimulationSampler:
    """Records a reading for each tracked simulation sensor whose interval
    has elapsed. No previous row counts as elapsed. Skips MQTT devices and
    devices with tracking off."""

    def __init__(self, repo: ReadingRepository, ingest: ReadingIngest) -> None:
        self._repo = repo
        self._ingest = ingest

    def run_once(self, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        recorded = 0
        for device in self._repo.list_simulation_tracked_devices():
            protocol = (device.default_config or {}).get("protocol", "simulation")
            if protocol != "simulation":
                continue

            last = self._repo.get_latest(device.id)
            if last is not None:
                elapsed = (now - last.recorded_at).total_seconds()
                if elapsed < device.sampling_interval_seconds:
                    continue

            self._ingest.record_read(device.id, now=now)
            recorded += 1
        return recorded