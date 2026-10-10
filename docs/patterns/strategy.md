# Strategy pattern: automation recommendations

## Problem

Deciding whether a zone needs water is an algorithm, and different growers want
different algorithms: some water only when the soil is clearly dry, others water
early. If the API handler or service contained `if strategy == "conservative": ...
elif strategy == "aggressive": ...`, every new algorithm would mean editing that
branching code, and the decision rules would be tangled up with HTTP and database
code.

## Interface

`AutomationStrategy.decide(context) -> Recommendation` is the one interface.

- `LocationAutomationContext` is plain data: the location id, the zone id, that
  zone's low/high thresholds, and the latest moisture (and optional light)
  reading among sensors assigned to that zone. It holds no ORM rows.
- `Recommendation` has an `action` (`irrigate` or `wait`), a `reason`, and an
  optional `score` (how far below the strategy's target the moisture is).

## Concrete strategies

- `ConservativeStrategy` irrigates only when moisture is below the zone's low
  threshold.
- `AggressiveStrategy` irrigates when moisture is below the midpoint of the
  zone's low and high thresholds.

With thresholds 0.30 to 0.60 and moisture 0.40, conservative says `wait` and
aggressive says `irrigate`: same context, different strategy, different answer.
A zone with no moisture sensor gets `wait` with the reason "no moisture sensor in
this zone". It never borrows an unassigned device's reading.

## Where in code

- `domain/automation/context.py` and `domain/automation/strategy.py` hold the
  context, the interface, the strategies and the key registry (`STRATEGIES`).
  There are no FastAPI, SQLAlchemy or Pydantic imports here.
- `application/automation/service.py` builds one context per zone from the
  repositories, picks the strategy from the key saved for the location, and maps
  each recommendation to a DTO. It never branches on the key.
- `infrastructure/persistence/automation_repository.py` and the
  `automation_rules` table store one strategy key per location
  (`location_id` is unique, `ON DELETE CASCADE`). I chose a dedicated table so
  `locations` stays free of automation concerns and `parameters` (JSONB) has room
  for per-strategy settings later.
- `interfaces/api/automation.py` saves a key (unknown key gives 400) and
  evaluates a location (missing location gives 404; no saved strategy gives 400).

## Exercise: add a third strategy

To add, for example, a `scheduled` strategy:

1. Add a class implementing `decide(context)` in `domain/automation/strategy.py`.
2. Register it in the `STRATEGIES` dict under its key.
3. Add a unit test with a fake `LocationAutomationContext`.

Nothing else changes: the service, the API, the database and the dashboard
dropdown all read the registry, so the new key appears and works on its own.