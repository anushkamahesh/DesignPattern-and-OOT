# Facade pattern: location overview

## Why one entry point

The dashboard overview needs data from four places: the location and its zones,
the devices assigned to those zones, the newest reading of each device, and the
saved automation strategy with its current recommendation. If the HTTP handler
or the React panel called each of those itself, every client would have to know
how the subsystems fit together and would have to stitch the answers into one
snapshot.

`LocationOverviewFacade.get_overview(location_id)` is the single entry point.
The handler `GET /api/locations/{location_id}/overview` depends only on the
facade, and the `#overview` panel makes one request per location it shows.

## Which subsystems it hides

- Locations and zones (`LocationRepository`).
- Assigned devices and the newest readings (`OverviewRepository`).
- The saved strategy key (`AutomationRepository`).
- Strategy evaluation (`AutomationService.evaluate`, which runs the strategy).

A small factory, `create_overview_facade`, builds those collaborators, so the
router does not import any repository.

## last_recommendation is computed, not stored

`last_recommendation` is computed on every GET by calling the existing
automation evaluate service when a strategy key is saved. It is not cached in a
new table, so the next GET always reflects the database. When no key is saved
the response is still HTTP 200, and `strategy_key` and `last_recommendation`
are both null.

Evaluate returns one recommendation per zone, but the overview has one
`last_recommendation`. The facade summarises them: the action is `irrigate` if
any zone says irrigate, otherwise `wait`, and the reason lists the zones that
drive that action. This only summarises evaluate's output. The decision itself
stays in the strategy classes, and the facade never calls `decide`.

## Query shape

1. Load the location and its zones.
2. One query for devices assigned to the location (`location_id` set and
   `zone_id` not null). Unassigned devices never appear.
3. One query for the newest reading of those device ids (`DISTINCT ON
   (device_id)`, ordered by `recorded_at` descending, served by the
   `(device_id, recorded_at)` index). There is no reading query per device.
4. One read of the saved strategy key.
5. Call evaluate only when a key exists.

Evaluate still loads the location again and looks up the latest moisture and
light once per zone. That lookup stays in the strategy service on purpose:
removing it would mean duplicating the evaluate logic in the facade.

`tracking_enabled` and `sampling_interval_seconds` on each reading summary are
copied from the device. Readings are not filtered by `source`, so a manual
read, the simulation sampler and an MQTT ingest all qualify.

## No new table

Everything the overview shows is already stored by Phases 2 to 6, so no
migration was needed. I skipped the optional SQL view: the existing tables are
enough.