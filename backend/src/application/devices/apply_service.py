from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional
from uuid import UUID

from src.application.devices.dto import ExecutionDto
from src.application.devices.service import ActuatorNotFoundError
from src.domain.actuators.ports import ActuatorPort
from src.infrastructure.adapters.actuators.logging_decorator import LoggingDecorator
from src.infrastructure.adapters.actuators.max_runtime_decorator import MaxRunTimeDecorator
from src.infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter


def build_actuator_port(
    get_state,
    record,
    clock: Optional[Callable[[], datetime]] = None,
    inner: Optional[ActuatorPort] = None,
) -> ActuatorPort:
    """Composition order: logging (outermost) -> max run time -> simulation adapter."""
    core = inner if inner is not None else SimulationActuatorAdapter()
    return LoggingDecorator(MaxRunTimeDecorator(core, get_state, clock), record)


def to_execution_dto(row) -> ExecutionDto:
    return ExecutionDto(
        id=row.id,
        device_id=row.device_id,
        success=row.success,
        policy_applied=list(row.policy_applied),
        message=row.message,
        created_at=row.created_at,
    )


class ActuatorApplyService:
    def __init__(self, state_repo, log_repo, clock=None, inner=None) -> None:
        self._states = state_repo
        self._log = log_repo
        self._clock = clock
        self._inner = inner

    def apply(self, device_id: UUID, command: str, payload: dict) -> ExecutionDto:
        if self._states.get_actuator(device_id) is None:
            raise ActuatorNotFoundError(f"actuator {device_id} not found")

        recorded: list = []

        def record(dev: UUID, success: bool, policies: list[str], message: Optional[str]) -> None:
            recorded.append(self._log.insert(dev, success, policies, message))

        port = build_actuator_port(
            self._states.get_state_info, record, self._clock, self._inner
        )
        # A blocked attempt raises PolicyViolationError after its row is written.
        port.apply(device_id, command, payload)
        return to_execution_dto(recorded[0])

    def list_executions(self, limit: int = 20) -> list[ExecutionDto]:
        return [to_execution_dto(r) for r in self._log.list_recent(limit)]