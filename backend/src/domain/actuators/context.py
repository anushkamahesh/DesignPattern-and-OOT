from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import src.domain.actuators.state as rules


@dataclass
class ActuatorContext:
    """An actuator's current state plus the guarded way to change it.
    A rejected transition leaves the state untouched."""

    device_id: UUID
    state: str = rules.INITIAL_STATE

    def __post_init__(self) -> None:
        rules.validate_state(self.state)

    @property
    def allowed_commands(self) -> list[str]:
        return rules.allowed_commands(self.state)

    @property
    def allowed_targets(self) -> list[str]:
        return rules.allowed_targets(self.state)

    def transition_to(self, target: str) -> str:
        rules.check_transition(self.state, target)  # raises before any change
        self.state = target
        return self.state

    def apply_command(self, command: str) -> str:
        return self.transition_to(rules.target_for_command(self.state, command))