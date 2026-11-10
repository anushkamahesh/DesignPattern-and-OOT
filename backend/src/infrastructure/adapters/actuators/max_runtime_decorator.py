from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable, Optional
from uuid import UUID

from src.domain.actuators.errors import PolicyViolationError
from src.domain.actuators.ports import ActuatorPort
from src.domain.actuators.state import RUNNING

MAX_RUN_TIME = timedelta(minutes=30)
POLICY_NAME = "maxRunTime"
BLOCKED_MESSAGE = "Max run time exceeded"

# (device_id) -> (state, updated_at) from actuator_states, or None when no row exists
StateLookup = Callable[[UUID], Optional[tuple[str, datetime]]]


class MaxRunTimeDecorator(ActuatorPort):
    """Rejects an apply when the persisted state is running and has been so for at
    least MAX_RUN_TIME (measured from actuator_states.updated_at). A blocked
    attempt never reaches the inner adapter."""

    def __init__(
        self,
        inner: ActuatorPort,
        get_state: StateLookup,
        clock: Optional[Callable[[], datetime]] = None,
        max_run_time: timedelta = MAX_RUN_TIME,
    ) -> None:
        self.inner = inner
        self._get_state = get_state
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._max = max_run_time

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        info = self._get_state(device_id)
        if info is not None:
            state, updated_at = info
            if state == RUNNING and self._clock() - updated_at >= self._max:
                raise PolicyViolationError(POLICY_NAME, BLOCKED_MESSAGE)
        self.inner.apply(device_id, command, payload)