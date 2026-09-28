from uuid import UUID

from src.application.locations.dto import (
    LocationConfigCreateRequest,
    LocationConfigResponse,
    LocationSummaryResponse,
    ZoneResponse,
)
from src.domain.locations.config_builder import LocationConfigBuilder
from src.domain.locations.entity import Location, LocationConfig, Zone


def build_config_from_request(req: LocationConfigCreateRequest) -> LocationConfig:
    builder = LocationConfigBuilder().set_name(req.location_name)
    for z in req.zones:
        builder.add_zone(
            z.name, z.moisture_threshold_low, z.moisture_threshold_high, z.schedule
        )
    return builder.build()


def to_zone_response(zone: Zone, location_id: UUID) -> ZoneResponse:
    return ZoneResponse(
        id=zone.id,
        location_id=location_id,
        name=zone.name,
        moisture_threshold_low=zone.moisture_threshold_low,
        moisture_threshold_high=zone.moisture_threshold_high,
        schedule=zone.schedule,
    )


def to_summary(location: Location) -> LocationSummaryResponse:
    return LocationSummaryResponse(id=location.id, name=location.name)


def to_config_response(location: Location) -> LocationConfigResponse:
    return LocationConfigResponse(
        location=to_summary(location),
        zones=[to_zone_response(z, location.id) for z in location.zones],
    )