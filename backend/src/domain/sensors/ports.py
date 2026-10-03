from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.domain.sensors.reading import Reading


class SensorPort(ABC):
    """Unified read operation. Application code depends on this, never on a
    specific adapter class (except the selector that picks one)."""

    @abstractmethod
    def read(
        self, device_id: UUID, device_type: str, config: dict, now: datetime
    ) -> Reading:
        raise NotImplementedError