from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class ActuatorPort(ABC):
    """Unified apply operation. Phase 9 wraps this with decorators."""

    @abstractmethod
    def apply(self, device_id: UUID, command: str, payload: dict) -> dict:
        raise NotImplementedError