from __future__ import annotations

from datetime import datetime
from uuid import UUID

from src.domain.sensors.reading import Reading

# Translates an inbound dict, e.g. {"value": 0.41, "unit": "vwc"}, into
# Reading. No broker connection here or anywhere in this phase; Phase 12
# wires a subscriber that calls translate() with the payload it receives.


class MqttSensorAdapter:
    @staticmethod
    def translate(device_id: UUID, payload: dict, now: datetime) -> Reading:
        return Reading(
            device_id=device_id,
            value=float(payload["value"]),
            unit=str(payload.get("unit", "")),
            source="mqtt",
            recorded_at=now,
        )