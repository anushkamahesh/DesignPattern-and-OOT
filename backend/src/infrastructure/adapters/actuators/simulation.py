from __future__ import annotations

from uuid import UUID

from src.domain.actuators.ports import ActuatorPort


class SimulationActuatorAdapter(ActuatorPort):
    """Stub apply: records intent only, no GPIO. Phase 9 wraps this port
    with decorators; Phase 10 adds real command flow."""

    def apply(self, device_id: UUID, command: str, payload: dict) -> dict:
        return {
            "device_id": str(device_id),
            "command": command,
            "payload": payload,
            "applied": True,
            "source": "simulation",
        }