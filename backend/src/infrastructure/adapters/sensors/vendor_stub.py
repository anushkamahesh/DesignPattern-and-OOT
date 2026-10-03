from __future__ import annotations

import random
from datetime import datetime, timezone
from uuid import UUID

from src.domain.sensors.ports import SensorPort
from src.domain.sensors.reading import Reading

# The vendor's own shape: a percentage (0-100) and an epoch-millisecond
# timestamp, not our domain's 0-1 VWC float with a tz-aware datetime.
# Translating that mismatch into Reading is the point of this adapter.


class VendorStubAdapter(SensorPort):
    """Accepts a vendor-shaped payload and translates it to Reading.
    source = "vendor". Stands in for a real vendor SDK; not the ESP32 path."""

    def read(
        self, device_id: UUID, device_type: str, config: dict, now: datetime
    ) -> Reading:
        raw = self._fetch_vendor_payload(now)
        return self.translate(device_id, raw)

    @staticmethod
    def _fetch_vendor_payload(now: datetime) -> dict:
        return {
            "value_pct": round(random.uniform(20.0, 60.0), 1),
            "ts_ms": int(now.timestamp() * 1000),
        }

    @staticmethod
    def translate(device_id: UUID, raw: dict) -> Reading:
        """Pure translation, kept separate so it is testable without
        generating a random payload first."""
        value = float(raw["value_pct"]) / 100.0
        recorded_at = datetime.fromtimestamp(raw["ts_ms"] / 1000, tz=timezone.utc)
        return Reading(
            device_id=device_id, value=value, unit="vwc", source="vendor", recorded_at=recorded_at
        )