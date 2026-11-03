State the intent of the State pattern in plain language. What problem appears when lifecycle is modelled as boolean flags and scattered if guards?
Note

Your Answer

(The State pattern lets an object behave differently depending on its current state. It keeps the rules in one place instead of using lots of if statements.)

Name the participants (context, state interface, concrete states, client). How does a successful command lead to a transition, and where do guards live?
Note

Your Answer

(ActuatorContext manages the current state and commands. TRANSITIONS defines the allowed moves, and ActuatorStateService loads and saves the state. If a command is not allowed, it raises IllegalTransitionError.)

What is allowed_commands (or equivalent) for? Why is exposing “what can I do now?” better than letting the UI guess from a raw state string?
Note

Your Answer

(allowed_commands tells us which commands are available in the current state. This keeps the rules in the backend instead of repeating them in the UI.)

B. This phase of the application
Which actuator states did you implement (for example idle, running, error)? Sketch the legal transitions (which command or event moves idle → running, running → idle, into error, and out of error).
Note

Your Answer

(The states are off, idle, running, error and maintenance. Each state has allowed transitions. For example, idle can move to running with start_pump, but running cannot move directly to off.)

Why is actuator state stored in actuator_states (or equivalent) rather than only in process memory? What must still be true after you restart the backend?
Note

Your Answer

(The state is saved in the actuator_states database table. This means the actuator keeps its state even after the backend restarts. I tested this by restarting the backend and checking the pump's state.)

An illegal transition must raise a domain error and must not update the database. Why? Which HTTP status is reasonable for that case (400 or 409), and why should the rule live in the domain rather than in React?
Note

Your Answer

(An illegal transition raises an error and does not change the database. HTTP 409 Conflict is suitable because the command conflicts with the current state.)

Device JSON gains state and allowed_commands. How does the dashboard use those fields (badges, disable illegal buttons)? How does this prepare Phase 10 Command?
Note

Your Answer

(The dashboard shows the current state with a coloured badge. It disables unavailable buttons using allowed_commands and allowed_targets. Phase 10 will reuse the same command names.)

C. Compare, contrast, and scenarios
Contrast State with Strategy. Both look like “context delegates to an object.” Who typically changes the active object, and is the variation a lifecycle or a selectable policy? Give a greenhouse example of each (this phase vs Phase 6).
Note

Your Answer

(State changes as the object's condition changes. Strategy lets the client choose an algorithm. For example, a pump changing from idle to running uses State, while choosing conservative irrigation uses Strategy.)

Contrast State with a pile of booleans (is_running, is_fault, is_maintenance). Why do illegal combinations of flags appear, and how do explicit state objects (or a transition table) prevent that?
Note

Your Answer

(Separate booleans can create conflicting states, such as running and having a fault at the same time. A single state value avoids this and makes transitions easier to control.)

A classmate puts HTTP status mapping or SQLAlchemy commits inside a concrete state class. Another state mutates a flag directly and skips transition / set_state. Explain why each is a trap.
Note

Your Answer

(Putting HTTP or database code inside a state class mixes different responsibilities and makes testing harder. Changing the state directly without transition_to is also risky because it bypasses the transition rules.)
