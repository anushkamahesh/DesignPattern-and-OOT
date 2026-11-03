Phase 6 — Strategy questions
Pattern / focus: Strategy.

Read first: Guide 06 · Requirements

How to answer
Use your own wording. Do not paste teaching-example types (for example shipping quotes) as if they were your greenhouse classes.
When a question asks about this application, refer to irrigation (or lighting) policies, location context, and the automation API from the lab.
Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
Write each answer inside the matching Your Answer note. Replace the placeholder; leave the question text unchanged.
A. Pattern
State the intent of Strategy in plain language. How does the context use a strategy, and why must “choose which algorithm” stay separate from “run the algorithm”?
Note

Your Answer

(Strategy lets us choose between different ways of doing the same task. The context uses the selected strategy to make a decision without knowing how it works internally. Choosing the strategy and running it separately makes the code easier to change and maintain.)

Name the participants (strategy, concrete strategies, context, client). What goes wrong when all policies live as if/elif inside the context (or inside an HTTP router)?
Note

Your Answer

(The participants are the strategy (common interface), concrete strategies (different implementations), context (provides the information needed), and client (chooses the strategy). If all the rules are inside if/elif statements, the code becomes harder to maintain because adding a new policy requires changing the same class or HTTP router.)

When should you use Strategy, and when should you skip it (one algorithm only; or the variation is a lifecycle mode rather than a chosen policy)?
Note

Your Answer

(Use Strategy when there are several ways to make a decision and we want to switch between them easily. Skip it if there is only one way to do the task. Also, use State instead when the behaviour changes because an object moves through different lifecycle stages.)

B. This phase of the application
In this lab, what does a strategy’s decide(context) return (action + reason)? Give a concrete difference you implemented (or were required to implement) between conservative and aggressive on the same moisture reading and zone thresholds.
Note

Your Answer

(The decide(context) method returns an action, such as irrigate or wait, and a reason for the decision. For example, with the same moisture reading and zone thresholds, a conservative strategy might wait, while an aggressive strategy might recommend irrigation sooner.)

Where do the numbers in LocationAutomationContext (or your equivalent) come from? Latest moisture may already be in sensor_readings from a manual read, the simulation sampler, or MQTT translation — why does this phase not add a scheduler or a broker? Why must strategies receive a plain context object, not SQLAlchemy rows or FastAPI types? Why are thresholds read from zones, not hardcoded in the strategy class?
Note

Your Answer

(The numbers in LocationAutomationContext come from the application's stored sensor readings and zone settings. This phase uses existing readings, so it does not need to add a scheduler or message broker. Strategies receive a simple context object so they do not depend on database or web framework details. Thresholds come from the zones because each zone can have different watering needs.)

The active strategy_key is persisted per location_id (for example in automation_rules). Why must POST .../automation/evaluate use the saved key rather than a key the client sends only in that request? What happens on the next evaluate after the operator changes strategy but moisture stays the same?
Note

Your Answer

(The API must use the saved strategy_key so the selected strategy stays consistent between requests. If the operator changes the strategy, the next evaluation uses the newly saved strategy. Even if the moisture reading stays the same, the recommendation may change.)

Strategy recommends (irrigate / wait). It should not itself start a pump. Why keep decide separate from execute? Which later pattern is meant to carry out the action?
Note

Your Answer

(A strategy should only recommend whether to irrigate or wait; it should not start the pump itself. Keeping decisions separate from execution makes the system safer and easier to test. The Command pattern is meant to carry out the action.)

C. Compare, contrast, and scenarios
Contrast Strategy with State (Phase 8). Both delegate to an object with the same shape. Who typically changes the active object, and is the variation a policy or a lifecycle?
Note

Your Answer

(Strategy is used when we want to choose between different policies, such as conservative and aggressive irrigation. The client or operator usually chooses the strategy. State is used when an object's behaviour changes because of its lifecycle, and the object typically changes its own state as events occur.)

Contrast Strategy with Adapter (Phase 5) and with Builder (Phase 4). Which one translates a foreign API, which one assembles a valid aggregate, and which one swaps an algorithm?
Note

Your Answer

(Adapter translates an external API into the format our application expects. Builder helps create a valid object or group of related objects. Strategy lets us switch between different algorithms or policies.)

A classmate writes one “mega-strategy” that still contains if conservative / if aggressive inside a single class. Another strategy class calls the actuator adapter to water immediately. Explain why each is a trap.
Note

Your Answer

(A mega-strategy is a trap because it still puts all the policies in one class, so adding or changing a policy becomes harder. A strategy that directly calls the actuator adapter is also a trap because it mixes decision-making with execution. Strategies should recommend an action, while another part of the system carries it out.)
