from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from src.domain.automation.context import LocationAutomationContext


class UnknownStrategyError(ValueError):
    """The strategy key is not registered."""


@dataclass(frozen=True)
class Recommendation:
    action: str  # "irrigate" | "wait"
    reason: str
    score: Optional[float] = None  # how far below the strategy's target the moisture is


def _no_reading() -> Recommendation:
    # A zone with no moisture sensor never borrows another device's reading.
    return Recommendation(action="wait", reason="no moisture sensor in this zone")


class AutomationStrategy(ABC):
    @abstractmethod
    def decide(self, context: LocationAutomationContext) -> Recommendation:
        raise NotImplementedError


class ConservativeStrategy(AutomationStrategy):
    """Irrigate only when moisture has dropped below the zone's low threshold."""

    def decide(self, context: LocationAutomationContext) -> Recommendation:
        moisture = context.latest_moisture
        if moisture is None:
            return _no_reading()
        if moisture < context.zone_low:
            return Recommendation(
                action="irrigate",
                reason=f"moisture {moisture:.2f} is below the low threshold {context.zone_low:.2f}",
                score=round(context.zone_low - moisture, 4),
            )
        return Recommendation(
            action="wait",
            reason=f"moisture {moisture:.2f} is not below the low threshold {context.zone_low:.2f}",
        )


class AggressiveStrategy(AutomationStrategy):
    """Irrigate as soon as moisture falls below the midpoint of the zone's range."""

    def decide(self, context: LocationAutomationContext) -> Recommendation:
        moisture = context.latest_moisture
        if moisture is None:
            return _no_reading()
        target = (context.zone_low + context.zone_high) / 2
        if moisture < target:
            return Recommendation(
                action="irrigate",
                reason=f"moisture {moisture:.2f} is below the midpoint {target:.2f}",
                score=round(target - moisture, 4),
            )
        return Recommendation(
            action="wait",
            reason=f"moisture {moisture:.2f} is not below the midpoint {target:.2f}",
        )


# Add a new strategy by writing a class above and registering it here.
STRATEGIES: dict[str, type[AutomationStrategy]] = {
    "conservative": ConservativeStrategy,
    "aggressive": AggressiveStrategy,
}


def available_strategy_keys() -> list[str]:
    return sorted(STRATEGIES)


def get_strategy(key: str) -> AutomationStrategy:
    try:
        return STRATEGIES[key]()
    except KeyError:
        raise UnknownStrategyError(
            f"unknown strategy '{key}'; known: {', '.join(available_strategy_keys())}"
        ) from None