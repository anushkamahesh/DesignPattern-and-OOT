Phase 9 — Decorator questions
Pattern / focus: Decorator.

Read first: Guide 09 · Requirements

How to answer
Use your own wording. Do not paste teaching-example types (for example HTTP client wrappers) as if they were your greenhouse classes.
When a question asks about this application, refer to ActuatorPort, policy decorators, and actuator_execution_log from the lab.
Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
Write each answer inside the matching Your Answer note. Replace the placeholder; leave the question text unchanged.
A. Pattern
State the intent of Decorator in plain language. Why is stacking wrappers a flexible alternative to a combinatorial explosion of subclasses (LoggingRetryMaxRuntimeActuator, …)?
Note

Your Answer

(Decorator adds behaviour to an object by wrapping it in another object with the same interface, so the caller can’t tell the difference. Stacking wrappers is flexible because each policy is one small class, and you combine them when you build the chain. With subclasses you’d need a class for every combination (logging only, logging plus max run time, and so on), and each new policy would double the number of classes.)

Name the participants (component, concrete component, decorator, concrete decorators). What interface does every decorator present to the caller, and why must that match the wrapped component?
Note

Your Answer

(The component is the interface, ActuatorPort. The concrete component is SimulationActuatorAdapter, the real thing at the centre. The decorators are LoggingDecorator and MaxRunTimeDecorator. Each holds another ActuatorPort and delegates to it. Every decorator presents the same apply(device_id, command, payload) interface as the thing it wraps. That has to match so a caller can use a decorated actuator exactly like a plain one, and so decorators can be stacked in any order.)

Order matters. Using logging and retry (or logging and max-run-time) as an example, explain how wrapping A around B can change what you observe compared with wrapping B around A.
Note

Your Answer

(Order changes what gets seen. In my chain, logging is outside max run time, so when max run time blocks an attempt, the logging wrapper still sees the failure and records it. If max run time were outside logging, the block would happen before logging was ever reached, so the blocked attempt would leave no row. With retry in the mix, logging outside retry records one row per logical call, while logging inside retry records one row per inner attempt.)

B. This phase of the application
What is ActuatorPort here, and which at least two decorators did you stack around the real adapter (for example logging and max run-time)? Where is the chain wired (composition root / factory), and why not inside the HTTP router?
Note

Your Answer

(ActuatorPort is the interface with one method, apply. I stacked LoggingDecorator and MaxRunTimeDecorator around SimulationActuatorAdapter, in the order logging, then max run time, then the adapter. The chain is built in build_actuator_port in application/devices/apply_service.py, and ActuatorApplyService calls it. It isn’t wired in the HTTP router because the router should only handle HTTP. If the chain were built there, changing the policies would mean editing web code, and the same chain couldn’t be reused by Phase 10’s commands or by tests.)

Max run-time can short-circuit: the inner adapter is never called. Why must a blocked attempt still produce a row in actuator_execution_log with success=false and the policy named in policy_applied?
Note

Your Answer

(A blocked attempt still has to produce a row because a refused command is an event someone needs to see, otherwise a command that was silently rejected looks like it was never sent. The row says success=false, with policy_applied set to ["maxRunTime", "logging"] and the message “Max run time exceeded”, so you can tell which policy blocked it and why.)

How does max run-time know the actuator has been running too long (for example actuator_states.updated_at from Phase 8)? Why is that data from State, not something the decorator should invent as a second lifecycle?
Note

Your Answer

(Max run time reads the actuator’s persisted state and actuator_states.updated_at from Phase 8. If the state is running and updated_at is 30 minutes or more in the past, it blocks. I made save_state refresh updated_at on every transition, so it marks the moment the actuator entered its current state. The data comes from State because State already owns the actuator’s lifecycle. If the decorator tracked its own “started at” time, there would be two sources of truth that could disagree.)

GET /api/actuators/executions feeds the dashboard execution log. Why persist attempts in the database instead of only printing to stdout? What should the UI show after a blocked attempt and a refresh?
Note

Your Answer

(Attempts are saved in actuator_execution_log so they survive a restart and can be shown in the UI, while stdout lines vanish when the container restarts and can’t be queried. After a blocked attempt and a refresh, the UI should still show a red “blocked” row with the policies maxRunTime and logging and the message “Max run time exceeded”)

C. Compare, contrast, and scenarios
Contrast Decorator with Adapter. Both wrap. One keeps the interface and adds behaviour; the other changes the interface and translates. Which is which in this greenhouse (Phase 9 vs Phase 5)?
Note

Your Answer

(Decorator keeps the interface and adds behaviour, and Adapter changes the interface by translating one shape into another. In the greenhouse, Phase 9’s logging and max-run-time wrappers are decorators: they present the same ActuatorPort and add policy around the call. Phase 5’s vendor and MQTT sensor adapters are adapters: they translate a vendor payload or an MQTT dict into our Reading.)

Contrast Decorator with inheritance of combined policies. How does composition let you add or remove a policy without a new subclass for every combination?
Note

Your Answer

(With inheritance, each combination of policies needs its own subclass, and the combination is fixed at coding time. With composition, each policy is a separate small class, and you pick the policies when you build the chain, so adding or removing one is a one-line change in build_actuator_port, with no new class for each combination.)

A classmate’s decorator changes the method signature “a little” (extra required argument, different return type). Another ignores wrap order and cannot explain whether logging runs once per logical call or per inner attempt. Explain why each is a trap.
Note

Your Answer

(A decorator that changes the signature (an extra required argument or a different return type) is a trap, because it no longer matches the interface it wraps, so callers can’t treat it like the plain component and decorators can’t be stacked freely. Ignoring wrap order is a trap because the order decides what is observed: you can’t say whether logging records once per logical call or once per inner attempt, and a policy that blocks a command may or may not leave a log row. Both make the behaviour unpredictable.)
