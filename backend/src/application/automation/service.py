from __future__ import annotations

from uuid import UUID

from src.application.automation.dto import (
    AutomationRuleResponse,
    EvaluationResponse,
    ZoneRecommendationResponse,
)
from src.domain.automation.context import LocationAutomationContext
from src.domain.automation.strategy import available_strategy_keys, get_strategy
from src.domain.locations.errors import LocationNotFoundError


class StrategyNotSetError(ValueError):
    """No strategy has been saved for this location yet."""


class AutomationService:
    def __init__(self, location_repo, automation_repo) -> None:
        self._locations = location_repo
        self._rules = automation_repo

    def list_strategies(self) -> list[str]:
        return available_strategy_keys()

    def _require_location(self, location_id: UUID):
        location = self._locations.get_location(location_id)
        if location is None:
            raise LocationNotFoundError(f"location {location_id} not found")
        return location

    def get_rule(self, location_id: UUID) -> AutomationRuleResponse:
        self._require_location(location_id)
        row = self._rules.get_rule(location_id)
        return AutomationRuleResponse(
            location_id=location_id, strategy_key=row.strategy_key if row else None
        )

    def save_rule(self, location_id: UUID, strategy_key: str) -> AutomationRuleResponse:
        self._require_location(location_id)
        get_strategy(strategy_key)  # raises UnknownStrategyError before anything is stored
        row = self._rules.upsert_rule(location_id, strategy_key)
        return AutomationRuleResponse(location_id=location_id, strategy_key=row.strategy_key)

    def evaluate(self, location_id: UUID) -> EvaluationResponse:
        location = self._require_location(location_id)
        rule = self._rules.get_rule(location_id)
        if rule is None:
            raise StrategyNotSetError("no strategy saved for this location; save one first")
        strategy = get_strategy(rule.strategy_key)

        results: list[ZoneRecommendationResponse] = []
        for zone in location.zones:
            moisture = self._rules.latest_zone_value(zone.id, "moisture")
            light = self._rules.latest_zone_value(zone.id, "light")
            context = LocationAutomationContext(
                location_id=location_id,
                zone_id=zone.id,
                zone_low=zone.moisture_threshold_low,
                zone_high=zone.moisture_threshold_high,
                latest_moisture=moisture,
                latest_light=light,
            )
            rec = strategy.decide(context)
            results.append(
                ZoneRecommendationResponse(
                    zone_id=zone.id,
                    zone_name=zone.name,
                    latest_moisture=moisture,
                    action=rec.action,
                    reason=rec.reason,
                    score=rec.score,
                )
            )
        return EvaluationResponse(
            location_id=location_id, strategy_key=rule.strategy_key, recommendations=results
        )