from __future__ import annotations

from typing import Callable, Optional
from uuid import UUID

from src.domain.actuators.errors import PolicyViolationError
from src.domain.actuators.ports import ActuatorPort

POLICY_NAME = "logging"

# (device_id, success, policy_applied, message) -> None
Recorder = Callable[[UUID, bool, list[str], Optional[str]], None]


class LoggingDecorator(ActuatorPort):
    """Outermost wrapper: records every attempt, whether it completed, was blocked
    by a policy, or failed inside the adapter, then lets the outcome pass through."""

    def __init__(self, inner: ActuatorPort, record: Recorder) -> None:
        self.inner = inner
        self._record = record

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        try:
            self.inner.apply(device_id, command, payload)
        except PolicyViolationError as exc:
            self._record(device_id, False, [exc.policy, POLICY_NAME], exc.message)
            raise
        except Exception as exc:
            self._record(device_id, False, [POLICY_NAME], str(exc))
            raise
        self._record(device_id, True, [POLICY_NAME], None)