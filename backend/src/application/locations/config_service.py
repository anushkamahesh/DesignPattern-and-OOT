from uuid import UUID

from src.application.locations.dto import (
    LocationConfigCreateRequest,
    LocationConfigResponse,
    LocationSummaryResponse,
    ZoneCreateRequest,
    ZoneResponse,
    ZoneUpdateRequest,
)
from src.application.locations.mappers import (
    build_config_from_request,
    to_config_response,
    to_zone_response,
)
from src.domain.locations.config_builder import (
    validate_zone_name,
    validate_zone_thresholds,
)
from src.domain.locations.entity import Zone
from src.domain.locations.errors import (
    ConfigurationError,
    LocationNotFoundError,
    ZoneNotFoundError,
)


class LocationConfigService:
    """Create/read/list/delete locations and manage zones on saved locations.
    Only create_location_config uses the builder."""

    def __init__(self, repo) -> None:
        self._repo = repo

    # ---- locations ----
    def create_location_config(self, req: LocationConfigCreateRequest) -> LocationConfigResponse:
        config = build_config_from_request(req)  # raises ConfigurationError before any write
        saved = self._repo.save_location_config(config)
        return to_config_response(saved)

    def list_locations(self) -> list[LocationSummaryResponse]:
        return [LocationSummaryResponse(id=i, name=n) for i, n in self._repo.list_locations()]

    def get_location_config(self, location_id: UUID) -> LocationConfigResponse:
        location = self._repo.get_location(location_id)
        if location is None:
            raise LocationNotFoundError(f"location {location_id} not found")
        return to_config_response(location)

    def delete_location(self, location_id: UUID) -> None:
        if not self._repo.delete_location(location_id):
            raise LocationNotFoundError(f"location {location_id} not found")

    # ---- zones ----
    @staticmethod
    def _check_unique(name: str, zones, exclude_id=None) -> None:
        for z in zones:
            if z.id != exclude_id and z.name.lower() == name.lower():
                raise ConfigurationError(f"duplicate zone name in this location: {name}")

    def add_zone(self, location_id: UUID, req: ZoneCreateRequest) -> ZoneResponse:
        location = self._repo.get_location(location_id)
        if location is None:
            raise LocationNotFoundError(f"location {location_id} not found")
        name = validate_zone_name(req.name)
        validate_zone_thresholds(req.moisture_threshold_low, req.moisture_threshold_high)
        self._check_unique(name, location.zones)
        zone = Zone(
            name=name,
            moisture_threshold_low=req.moisture_threshold_low,
            moisture_threshold_high=req.moisture_threshold_high,
            schedule=req.schedule or {},
        )
        return to_zone_response(self._repo.add_zone(location_id, zone), location_id)

    def update_zone(self, location_id: UUID, zone_id: UUID, req: ZoneUpdateRequest) -> ZoneResponse:
        location = self._repo.get_location(location_id)
        if location is None:
            raise LocationNotFoundError(f"location {location_id} not found")
        existing = next((z for z in location.zones if z.id == zone_id), None)
        if existing is None:
            raise ZoneNotFoundError(f"zone {zone_id} not found in location {location_id}")

        name = validate_zone_name(req.name) if req.name is not None else existing.name
        low = req.moisture_threshold_low if req.moisture_threshold_low is not None else existing.moisture_threshold_low
        high = req.moisture_threshold_high if req.moisture_threshold_high is not None else existing.moisture_threshold_high
        schedule = req.schedule if req.schedule is not None else existing.schedule
        validate_zone_thresholds(low, high)
        self._check_unique(name, location.zones, exclude_id=zone_id)

        updated = self._repo.update_zone(
            location_id,
            Zone(id=zone_id, name=name, moisture_threshold_low=low,
                 moisture_threshold_high=high, schedule=schedule),
        )
        if updated is None:
            raise ZoneNotFoundError(f"zone {zone_id} not found in location {location_id}")
        return to_zone_response(updated, location_id)

    def delete_zone(self, location_id: UUID, zone_id: UUID) -> None:
        location = self._repo.get_location(location_id)
        if location is None:
            raise LocationNotFoundError(f"location {location_id} not found")
        if not any(z.id == zone_id for z in location.zones):
            raise ZoneNotFoundError(f"zone {zone_id} not found in location {location_id}")
        if len(location.zones) <= 1:
            raise ConfigurationError("cannot delete the last zone of a location")
        if not self._repo.delete_zone(location_id, zone_id):
            raise ZoneNotFoundError(f"zone {zone_id} not found in location {location_id}")