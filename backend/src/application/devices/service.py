from __future__ import annotations

from uuid import UUID

from src.application.devices.dto import ActuatorDto
from src.domain.actuators.context import ActuatorContext
from src.domain.actuators.state import INITIAL_STATE


class ActuatorNotFoundError(LookupError):
    """No actuator with that id (a sensor id counts as not found)."""


def _to_dto(device, stored_state: str | None) -> ActuatorDto:
    # No stored row yet reads as the initial state. Reads never write.
    ctx = ActuatorContext(device.id, stored_state or INITIAL_STATE)
    return ActuatorDto(
        id=device.id,
        device_type=device.device_type,
        role=device.role,
        display_name=device.display_name,
        device_family=device.device_family,
        zone_id=device.zone_id,
        location_id=device.location_id,
        state=ctx.state,
        allowed_commands=ctx.allowed_commands,
        allowed_targets=ctx.allowed_targets,
    )


class ActuatorStateService:
    def __init__(self, repo) -> None:
        self._repo = repo

    def list_actuators(self) -> list[ActuatorDto]:
        return [_to_dto(device, state) for device, state in self._repo.list_actuators()]

    def get_actuator(self, device_id: UUID) -> ActuatorDto:
        found = self._repo.get_actuator(device_id)
        if found is None:
            raise ActuatorNotFoundError(f"actuator {device_id} not found")
        return _to_dto(*found)

    def transition(self, device_id: UUID, target: str) -> ActuatorDto:
        found = self._repo.get_actuator(device_id)
        if found is None:
            raise ActuatorNotFoundError(f"actuator {device_id} not found")
        device, stored_state = found

        ctx = ActuatorContext(device.id, stored_state or INITIAL_STATE)
        ctx.transition_to(target)  # raises before anything is saved
        self._repo.save_state(device.id, ctx.state)
        return _to_dto(device, ctx.state)