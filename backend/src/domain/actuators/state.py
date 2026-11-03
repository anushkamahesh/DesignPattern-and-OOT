from __future__ import annotations

OFF = "off"
IDLE = "idle"
RUNNING = "running"
ERROR = "error"
MAINTENANCE = "maintenance"

STATES: tuple[str, ...] = (OFF, IDLE, RUNNING, ERROR, MAINTENANCE)
INITIAL_STATE = IDLE

# state -> {command: target state}. This table is the only place the lifecycle
# rules live; anything not listed is illegal. Within one state each command leads
# to a different target, so a target maps back to exactly one command.
# Phase 10 (Command) reuses these command names.
TRANSITIONS: dict[str, dict[str, str]] = {
    OFF: {"power_on": IDLE, "report_fault": ERROR},
    IDLE: {
        "start_pump": RUNNING,
        "power_off": OFF,
        "enter_maintenance": MAINTENANCE,
        "report_fault": ERROR,
    },
    RUNNING: {"stop_pump": IDLE, "report_fault": ERROR},
    ERROR: {"reset": IDLE, "power_off": OFF},
    MAINTENANCE: {"exit_maintenance": IDLE, "report_fault": ERROR},
}


class UnknownStateError(ValueError):
    """The state name is not one of the known states."""


class IllegalTransitionError(ValueError):
    """The requested move is not in the transition table."""


def validate_state(state: str) -> str:
    if state not in TRANSITIONS:
        raise UnknownStateError(f"unknown state '{state}'; known: {', '.join(STATES)}")
    return state


def allowed_commands(state: str) -> list[str]:
    return list(TRANSITIONS[validate_state(state)])


def allowed_targets(state: str) -> list[str]:
    return list(TRANSITIONS[validate_state(state)].values())


def target_for_command(state: str, command: str) -> str:
    table = TRANSITIONS[validate_state(state)]
    try:
        return table[command]
    except KeyError:
        raise IllegalTransitionError(
            f"command '{command}' is not allowed while {state}; allowed: {', '.join(table)}"
        ) from None


def check_transition(state: str, target: str) -> None:
    validate_state(state)
    validate_state(target)
    if target not in TRANSITIONS[state].values():
        raise IllegalTransitionError(
            f"cannot move from {state} to {target}; "
            f"allowed targets from {state}: {', '.join(allowed_targets(state))}"
        )