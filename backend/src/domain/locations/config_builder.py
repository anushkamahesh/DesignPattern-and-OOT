from __future__ import annotations

from src.domain.locations.entity import Location, LocationConfig, Zone
from src.domain.locations.errors import ConfigurationError

MOISTURE_MIN = 0.0
MOISTURE_MAX = 1.0


def validate_zone_thresholds(low: float, high: float) -> None:
    if not (MOISTURE_MIN <= low <= MOISTURE_MAX):
        raise ConfigurationError(
            f"moisture_threshold_low must be between {MOISTURE_MIN} and {MOISTURE_MAX}"
        )
    if not (MOISTURE_MIN <= high <= MOISTURE_MAX):
        raise ConfigurationError(
            f"moisture_threshold_high must be between {MOISTURE_MIN} and {MOISTURE_MAX}"
        )
    if not (low < high):
        raise ConfigurationError(
            "moisture_threshold_low must be strictly less than moisture_threshold_high"
        )


def validate_zone_name(name: str) -> str:
    cleaned = (name or "").strip()
    if not cleaned:
        raise ConfigurationError("zone name is required")
    return cleaned


class LocationConfigBuilder:
    """Builds a new, unsaved LocationConfig. Sets the name and adds zones only.
    It has no method to attach devices: assignment happens after zones are saved."""

    def __init__(self) -> None:
        self._name: str | None = None
        self._zones: list[Zone] = []

    def set_name(self, name: str) -> "LocationConfigBuilder":
        self._name = (name or "").strip()
        return self

    def add_zone(
        self,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict | None = None,
    ) -> "LocationConfigBuilder":
        cleaned = validate_zone_name(name)
        validate_zone_thresholds(moisture_threshold_low, moisture_threshold_high)
        self._zones.append(
            Zone(
                name=cleaned,
                moisture_threshold_low=moisture_threshold_low,
                moisture_threshold_high=moisture_threshold_high,
                schedule=schedule or {},
            )
        )
        return self

    def build(self) -> LocationConfig:
        if not self._name:
            raise ConfigurationError("location name is required")
        if not self._zones:
            raise ConfigurationError("at least one zone is required")
        seen: set[str] = set()
        for zone in self._zones:
            key = zone.name.lower()
            if key in seen:
                raise ConfigurationError(f"duplicate zone name in this location: {zone.name}")
            seen.add(key)
        return LocationConfig(location=Location(name=self._name, zones=tuple(self._zones)))