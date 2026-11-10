import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.application.devices.apply_service import build_actuator_port
from src.domain.actuators.errors import PolicyViolationError
from src.domain.actuators.ports import ActuatorPort
from src.infrastructure.adapters.actuators.logging_decorator import LoggingDecorator
from src.infrastructure.adapters.actuators.max_runtime_decorator import MaxRunTimeDecorator
from src.infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter

NOW = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)


class FakeInner(ActuatorPort):
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def apply(self, device_id, command, payload):
        if self.fail:
            raise RuntimeError("boom")
        self.calls.append((device_id, command, payload))


def make_chain(state, inner=None):
    records = []
    inner = inner if inner is not None else FakeInner()
    chain = build_actuator_port(
        get_state=lambda device_id: state,
        record=lambda *args: records.append(args),
        clock=lambda: NOW,
        inner=inner,
    )
    return chain, inner, records


def running_for(minutes):
    return ("running", NOW - timedelta(minutes=minutes))


@pytest.mark.parametrize("minutes", [30, 31, 120])
def test_blocked_when_running_for_30_minutes_or_more(minutes):
    chain, inner, records = make_chain(running_for(minutes))
    device = uuid.uuid4()
    with pytest.raises(PolicyViolationError):
        chain.apply(device, "stop_pump", {})
    assert inner.calls == []  # the inner adapter was never reached
    assert records == [(device, False, ["maxRunTime", "logging"], "Max run time exceeded")]


def test_not_blocked_just_under_30_minutes():
    chain, inner, records = make_chain(running_for(29))
    device = uuid.uuid4()
    chain.apply(device, "stop_pump", {})
    assert len(inner.calls) == 1
    assert records == [(device, True, ["logging"], None)]


@pytest.mark.parametrize("state", ["idle", "off", "error", "maintenance"])
def test_only_the_running_state_is_limited(state):
    chain, inner, records = make_chain((state, NOW - timedelta(hours=5)))
    chain.apply(uuid.uuid4(), "anything", {})
    assert len(inner.calls) == 1
    assert records[0][1] is True


def test_no_state_row_is_not_blocked():
    chain, inner, records = make_chain(None)
    chain.apply(uuid.uuid4(), "start_pump", {})
    assert len(inner.calls) == 1
    assert records[0][1:] == (True, ["logging"], None)


def test_success_records_logging_only_and_forwards_the_command():
    chain, inner, records = make_chain(("idle", NOW))
    device = uuid.uuid4()
    chain.apply(device, "start_pump", {"seconds": 5})
    assert inner.calls == [(device, "start_pump", {"seconds": 5})]
    assert records == [(device, True, ["logging"], None)]


def test_unknown_command_is_forwarded_and_succeeds():
    chain, inner, records = make_chain(("idle", NOW))
    device = uuid.uuid4()
    chain.apply(device, "banana", {})
    assert inner.calls == [(device, "banana", {})]
    assert records[0][1] is True


def test_inner_failure_is_recorded_and_re_raised():
    chain, _, records = make_chain(("idle", NOW), inner=FakeInner(fail=True))
    device = uuid.uuid4()
    with pytest.raises(RuntimeError):
        chain.apply(device, "start_pump", {})
    assert records == [(device, False, ["logging"], "boom")]


def test_every_attempt_is_logged_exactly_once():
    chain, _, records = make_chain(running_for(60))
    for _ in range(3):
        with pytest.raises(PolicyViolationError):
            chain.apply(uuid.uuid4(), "stop_pump", {})
    assert len(records) == 3


def test_decorators_share_the_port_and_stack_in_order():
    inner = FakeInner()
    chain, _, _ = make_chain(("idle", NOW), inner=inner)
    assert isinstance(chain, ActuatorPort) and isinstance(chain, LoggingDecorator)
    assert isinstance(chain.inner, ActuatorPort) and isinstance(chain.inner, MaxRunTimeDecorator)
    assert chain.inner.inner is inner


def test_default_core_is_the_simulation_adapter():
    chain = build_actuator_port(get_state=lambda d: None, record=lambda *a: None)
    assert isinstance(chain.inner.inner, SimulationActuatorAdapter)


def test_simulation_adapter_records_intent_and_returns_none():
    adapter = SimulationActuatorAdapter()
    device = uuid.uuid4()
    assert adapter.apply(device, "start_pump", {"x": 1}) is None
    assert adapter.applied == [{"device_id": str(device), "command": "start_pump", "payload": {"x": 1}}]