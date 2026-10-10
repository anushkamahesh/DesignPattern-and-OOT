import uuid

import pytest

from src.domain.automation.context import LocationAutomationContext
from src.domain.automation.strategy import (
    AggressiveStrategy,
    ConservativeStrategy,
    UnknownStrategyError,
    available_strategy_keys,
    get_strategy,
)


def ctx(moisture, low=0.3, high=0.6):
    return LocationAutomationContext(
        location_id=uuid.uuid4(),
        zone_id=uuid.uuid4(),
        zone_low=low,
        zone_high=high,
        latest_moisture=moisture,
    )


def test_same_context_different_strategies_differ():
    context = ctx(0.40)  # above low (0.30), below midpoint (0.45)
    assert ConservativeStrategy().decide(context).action == "wait"
    assert AggressiveStrategy().decide(context).action == "irrigate"


def test_both_irrigate_below_low_threshold():
    context = ctx(0.20)
    assert ConservativeStrategy().decide(context).action == "irrigate"
    assert AggressiveStrategy().decide(context).action == "irrigate"


def test_both_wait_above_midpoint():
    context = ctx(0.55)
    assert ConservativeStrategy().decide(context).action == "wait"
    assert AggressiveStrategy().decide(context).action == "wait"


def test_no_moisture_reading_waits_with_reason_for_both():
    for strategy in (ConservativeStrategy(), AggressiveStrategy()):
        rec = strategy.decide(ctx(None))
        assert rec.action == "wait"
        assert "no moisture sensor" in rec.reason


def test_irrigate_recommendation_has_score():
    assert ConservativeStrategy().decide(ctx(0.20)).score == pytest.approx(0.10)


def test_registry_returns_instances_and_rejects_unknown_key():
    assert isinstance(get_strategy("conservative"), ConservativeStrategy)
    assert isinstance(get_strategy("aggressive"), AggressiveStrategy)
    assert available_strategy_keys() == ["aggressive", "conservative"]
    with pytest.raises(UnknownStrategyError):
        get_strategy("nope")