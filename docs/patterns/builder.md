# Builder pattern: location configuration

## Intent in this project

A location configuration is a location with a name and one or more zones, each
with moisture thresholds and a schedule. `LocationConfigBuilder` assembles that
configuration step by step (`set_name`, `add_zone`) and `build()` returns a
complete, immutable, unsaved `LocationConfig`, or raises `ConfigurationError`.
Nothing is written to the database until `build()` succeeds.

## Why this is Builder, not Factory Method or Abstract Factory

- **Factory Method** (Phase 2) decides which single product class to create,
  such as a moisture sensor or a light sensor. There is one object and the
  question is which type.
- **Abstract Factory** (Phase 3) creates a family of matching objects
  (simulation or edge sensors and actuators). The question is which family.
- **Builder** (Phase 4) constructs one complex object from many parts, in
  steps, and validates the whole before handing it over. The question is how
  to assemble it correctly. The zones are parts of one location, and the
  result is only valid as a whole (at least one zone, unique zone names).

## Where validation lives

Validation lives in the domain layer, not in the API.

- `domain/locations/config_builder.py` holds the rules: non-empty location
  name, at least one zone, non-empty zone names, unique zone names within a
  location (case-insensitive), thresholds in 0.0-1.0, low strictly less than
  high.
- The zone rules are exposed as `validate_zone_name` and
  `validate_zone_thresholds`. Adding or editing a zone on a saved location
  calls the same functions, so the rules exist in one place.
- The application layer only maps DTOs to builder calls. The API layer turns
  `ConfigurationError` into a 400 response. Invalid configurations are rejected
  before any database write.
- The domain package imports nothing from FastAPI, SQLAlchemy or Pydantic.

## Why `location_id`

The product is still a smart greenhouse, but the relational resource is a
location: a site that contains zones. Zones and devices reference
`location_id`, and `greenhouse_id` is not used in any schema or endpoint. On
assignment, `devices.location_id` is copied from the zone, never sent by the
client, so a device can never point at a zone and a different location.

## Why device assignment is not a builder method

- Devices already exist from Phases 2-3. They are not parts of a new location.
- A zone has no id until the configuration is saved, so a builder cannot refer
  to a zone that does not exist yet.
- Moving a device is an update to one row on a saved location. Rebuilding the
  whole location to move a device would be wrong and wasteful.

Assignment therefore lives in `ZoneAssignmentService`, which sets or clears
`devices.zone_id` and `devices.location_id` in one transaction. The same goes
for listing and deleting locations and for adding, editing or deleting a zone
on a saved location: none of them call the builder.

## Behaviours worth remembering

- Deleting a location cascades to its zones; its devices stay and end up
  unassigned (`zone_id` and `location_id` null).
- Deleting a zone first clears `zone_id` and `location_id` on its devices,
  because `ON DELETE SET NULL` on `zone_id` alone would leave `location_id`
  pointing at the location.
- The last zone of a location cannot be deleted (400).
- `GET /api/locations` returns newest first.