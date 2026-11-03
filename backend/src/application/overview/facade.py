from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from src.application.automation.dto import ZoneRecommendationResponse
from src.application.automation.service import AutomationService, StrategyNotSetError
from src.application.overview.dto import (
    LocationOverviewDto,
    OverviewDevice,
    OverviewDeviceCounts,
    OverviewLocation,
    OverviewReading,
    OverviewRecommendation,
    OverviewZone,
)
from src.domain.automation.strategy import UnknownStrategyError
from src.domain.locations.errors import LocationNotFoundError
from src.infrastructure.persistence.automation_repository import AutomationRepository
from src.infrastructure.persistence.location_repository import LocationRepository
from src.infrastructure.persistence.overview_repository import OverviewRepository


def summarize_recommendations(
    recommendations: list[ZoneRecommendationResponse],
) -> OverviewRecommendation:
    """Collapse evaluate's per-zone recommendations into one summary. This does
    not decide anything: the policy already ran inside the strategy.
    irrigate if any zone says irrigate, otherwise wait; the reason lists the
    zones that drive that action."""
    if not recommendations:
        return OverviewRecommendation(action="wait", reason="no zones to evaluate")
    irrigating = [r for r in recommendations if r.action == "irrigate"]
    driving = irrigating or list(recommendations)
    return OverviewRecommendation(
        action="irrigate" if irrigating else "wait",
        reason="; ".join(f"{r.zone_name}: {r.reason}" for r in driving),
    )


class LocationOverviewFacade:
    """Single entry point for the dashboard overview. Hides the location and
    zone repository, the assigned-device and newest-reading queries, the saved
    strategy key, and the automation evaluate service."""

    def __init__(
        self,
        locations: LocationRepository,
        overview: OverviewRepository,
        automation_rules: AutomationRepository,
        automation_service: AutomationService,
    ) -> None:
        self._locations = locations
        self._overview = overview
        self._rules = automation_rules
        self._automation = automation_service

    def get_overview(self, location_id: UUID) -> LocationOverviewDto:
        location = self._locations.get_location(location_id)
        if location is None:
            raise LocationNotFoundError(f"location {location_id} not found")

        devices = self._overview.list_assigned_devices(location_id)
        newest = {
            r.device_id: r
            for r in self._overview.latest_readings([d.id for d in devices])
        }

        by_zone = defaultdict(list)
        for device in devices:
            by_zone[device.zone_id].append(device)

        counts = {"sensor": 0, "actuator": 0}
        zones: list[OverviewZone] = []
        for zone in location.zones:
            zone_devices = by_zone.get(zone.id, [])
            for d in zone_devices:
                if d.role in counts:
                    counts[d.role] += 1
            zones.append(
                OverviewZone(
                    id=zone.id,
                    name=zone.name,
                    moisture_threshold_low=zone.moisture_threshold_low,
                    moisture_threshold_high=zone.moisture_threshold_high,
                    devices=[
                        OverviewDevice(
                            id=d.id,
                            device_type=d.device_type,
                            role=d.role,
                            display_name=d.display_name,
                        )
                        for d in zone_devices
                    ],
                    latest_readings=[
                        OverviewReading(
                            device_id=d.id,
                            value=newest[d.id].value,
                            unit=newest[d.id].unit,
                            recorded_at=newest[d.id].recorded_at,
                            tracking_enabled=d.tracking_enabled,
                            sampling_interval_seconds=d.sampling_interval_seconds,
                        )
                        for d in zone_devices
                        if d.id in newest
                    ],
                )
            )

        rule = self._rules.get_rule(location_id)
        strategy_key = rule.strategy_key if rule else None
        last_recommendation = None
        if strategy_key:
            try:
                evaluation = self._automation.evaluate(location_id)
                last_recommendation = summarize_recommendations(evaluation.recommendations)
            except (StrategyNotSetError, UnknownStrategyError):
                last_recommendation = None  # key vanished or is no longer registered

        return LocationOverviewDto(
            location=OverviewLocation(id=location.id, name=location.name),
            device_counts=OverviewDeviceCounts(**counts),
            zones=zones,
            strategy_key=strategy_key,
            last_recommendation=last_recommendation,
        )


def create_overview_facade(session) -> LocationOverviewFacade:
    """Wires the facade to its repositories, so the HTTP handler never has to."""
    locations = LocationRepository(session)
    rules = AutomationRepository(session)
    return LocationOverviewFacade(
        locations=locations,
        overview=OverviewRepository(session),
        automation_rules=rules,
        automation_service=AutomationService(locations, rules),
    )