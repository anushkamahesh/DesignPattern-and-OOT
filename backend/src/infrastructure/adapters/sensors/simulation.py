from __future__ import annotations

import random
from datetime import datetime
from uuid import UUID

from src.domain.sensors.ports import SensorPort
from src.domain.sensors.reading import Reading

# device_type -> (low, high, unit)
RANGES: dict[str, tuple[float, float, str]] = {
    "moisture": (0.2, 0.6, "vwc"),
    "light": (200.0, 2000.0, "lux"),
}
DEFAULT_RANGE: tuple[float, float, str] = (0.0, 1.0, "unit")


class SimulationSensorAdapter(SensorPort):
    """Generates a plausible value in code. source = "simulation"."""

    def read(
        self, device_id: UUID, device_type: str, config: dict, now: datetime
    ) -> Reading:
        low, high, unit = RANGES.get(device_type, DEFAULT_RANGE)
        value = round(random.uniform(low, high), 4)
        return Reading(
            device_id=device_id, value=value, unit=unit, source="simulation", recorded_at=now
        )