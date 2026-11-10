from __future__ import annotations

from uuid import UUID

from src.domain.actuators.ports import ActuatorPort


class SimulationActuatorAdapter(ActuatorPort):
    """Innermost component: records intent only, no GPIO. The command is not
    validated here; an unknown command is simply recorded."""

    def __init__(self) -> None:
        self.applied: list[dict] = []

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        self.applied.append(
            {"device_id": str(device_id), "command": command, "payload": payload}
        )