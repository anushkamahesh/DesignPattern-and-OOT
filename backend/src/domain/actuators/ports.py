from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class ActuatorPort(ABC):
    """Unified apply operation. The core adapter and every decorator implement
    this same port, so callers never know how many wrappers are stacked."""

    @abstractmethod
    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        raise NotImplementedError