import uuid

import pytest

import src.domain.actuators.state as rules
from src.domain.actuators.context import ActuatorContext

# Written out independently of the table, as the specification of the rules.
LEGAL = [
    ("off", "idle"), ("off", "error"),
    ("idle", "running"), ("idle", "off"), ("idle", "maintenance"), ("idle", "error"),
    ("running", "idle"), ("running", "error"),
    ("error", "idle"), ("error", "off"),
    ("maintenance", "idle"), ("maintenance", "error"),
]
ILLEGAL = [(a, b) for a in rules.STATES for b in rules.STATES if (a, b) not in LEGAL]


def ctx(state):
    return ActuatorContext(uuid.uuid4(), state)


def test_there_are_twelve_legal_and_thirteen_illegal_edges():
    assert len(LEGAL) == 12
    assert len(ILLEGAL) == 13


@pytest.mark.parametrize("start,target", LEGAL)
def test_legal_transition_changes_state(start, target):
    c = ctx(start)
    assert c.transition_to(target) == target
    assert c.state == target


@pytest.mark.parametrize("start,target", ILLEGAL)
def test_illegal_transition_raises_and_keeps_state(start, target):
    c = ctx(start)
    with pytest.raises(rules.IllegalTransitionError):
        c.transition_to(target)
    assert c.state == start


def test_every_state_except_error_can_report_a_fault():
    for state in rules.STATES:
        if state == "error":
            continue
        assert ctx(state).apply_command("report_fault") == "error"


def test_allowed_commands_depend_on_state():
    assert set(ctx("idle").allowed_commands) == {
        "start_pump", "power_off", "enter_maintenance", "report_fault",
    }
    assert set(ctx("running").allowed_commands) == {"stop_pump", "report_fault"}
    assert "start_pump" not in ctx("running").allowed_commands


def test_command_that_is_not_allowed_is_rejected():
    c = ctx("running")
    with pytest.raises(rules.IllegalTransitionError):
        c.apply_command("start_pump")
    assert c.state == "running"


def test_commands_move_through_the_pump_cycle():
    c = ctx("idle")
    assert c.apply_command("start_pump") == "running"
    assert c.apply_command("stop_pump") == "idle"


def test_allowed_targets_match_the_commands():
    for state in rules.STATES:
        expected = [rules.TRANSITIONS[state][cmd] for cmd in rules.allowed_commands(state)]
        assert rules.allowed_targets(state) == expected


def test_each_command_leads_to_a_different_target_within_a_state():
    for state, table in rules.TRANSITIONS.items():
        assert len(set(table.values())) == len(table), state


def test_unknown_state_or_target_is_rejected():
    with pytest.raises(rules.UnknownStateError):
        ActuatorContext(uuid.uuid4(), "banana")
    with pytest.raises(rules.UnknownStateError):
        ctx("idle").transition_to("banana")


def test_new_actuators_start_idle():
    assert ActuatorContext(uuid.uuid4()).state == "idle"