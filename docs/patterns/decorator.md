# Decorator pattern: actuator policies

## Problem

Applying a command to an actuator needs more than the apply itself: every attempt
should be recorded, and a pump that has been running too long should be refused.
Putting that into the adapter would mix hardware concerns with policy, and
inheritance would make it worse: `LoggedActuator`, `MaxRunTimeActuator` and
`LoggedMaxRunTimeActuator` would each need a class, and every new policy would
double the number of combinations.

## Wrapping

`ActuatorPort.apply(device_id, command, payload)` is the one interface. The core
adapter and every decorator implement it, and a decorator holds another
`ActuatorPort` and delegates to it. Callers use the port and never know how many
wrappers are stacked.

- `SimulationActuatorAdapter` is the innermost component: it records the intent and
  does nothing else. It does not validate the command.
- `MaxRunTimeDecorator` refuses to apply when the persisted state is `running` and
  `actuator_states.updated_at` is at least 30 minutes before the clock. It raises
  `PolicyViolationError` and does not call the inner adapter. `updated_at` is the
  moment the actuator entered its current state, because `save_state` refreshes it
  on every transition.
- `LoggingDecorator` is the outermost wrapper. It records every attempt in
  `actuator_execution_log` and then lets the outcome pass through unchanged.

## Order

`build_actuator_port` composes logging, then max run time, then the simulation
adapter. Logging has to be outermost: a blocked attempt never reaches the inner
adapter, so only the outer wrapper still sees it and can record it. If max run
time were outside logging, a blocked attempt would leave no row.

## What a row looks like

| Attempt | success | policy_applied | message |
|---|---|---|---|
| Completed | true | `["logging"]` | null |
| Blocked by max run time | false | `["maxRunTime", "logging"]` | `Max run time exceeded` |
| Failed inside the adapter | false | `["logging"]` | the error text |

Any command string is forwarded, and an unknown one still succeeds unless max run
time blocks it. Phase 10 (Command) will check the command against
`allowed_commands`.

## Where in code

- `domain/actuators/ports.py` and `domain/actuators/errors.py` hold the port and
  `PolicyViolationError`.
- `infrastructure/adapters/actuators/` holds `simulation.py`,
  `max_runtime_decorator.py` and `logging_decorator.py`.
- `application/devices/apply_service.py` composes the chain per request and maps
  rows to DTOs.
- `infrastructure/persistence/execution_log_repository.py` and the
  `actuator_execution_log` table store the attempts, so the log survives restarts.
- `GET /api/actuators/executions` lists them newest first. A demo route,
  `POST /api/actuators/{id}/apply`, sends a command through the chain until
  Phase 10 replaces it.

## Decorator vs inheritance

Inheritance fixes the combination of behaviours at compile time and needs a class
per combination. Decorators combine at runtime: each policy is one small class,
and the stack is chosen where the chain is built. Removing a policy is a one-line
change, and a policy can be tested alone with a fake inner port.

## Exercise: add a third policy

To add a `cooldown` decorator that refuses a second `start_pump` within a minute:
write a class that takes an inner `ActuatorPort`, raises `PolicyViolationError`
with its own policy name, and otherwise delegates; then insert it in
`build_actuator_port` between logging and the adapter. The logging decorator
already records whichever policy name the error carries.