Phase 4 — Builder questions
Pattern / focus: Builder.

Read first: Guide 04 · Requirements

How to answer
Use your own wording. Do not paste teaching-example types (for example ramen orders) as if they were your greenhouse classes.
When a question asks about this application, refer to locations, zones, location_id, and the configuration wizard from the lab.
Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
Write each answer inside the matching Your Answer note. Replace the placeholder; leave the question text unchanged.
A. Pattern
State the intent of Builder in plain language. Why does construction of a complex object need stepwise assembly and validation at the end (build()), instead of a telescoping constructor or a half-filled dict written straight to the database?
Note

Your Answer

(Builder is used to create a complex object step by step. It makes it easier to add the location and its zones and check that everything is valid before creating the final object. A big constructor or half-filled dictionary can easily miss required values or allow invalid data into the database.)

Name the main participants (product, builder, optional director, client). Until build() succeeds, is the intermediate object a finished domain product? Why does that distinction matter?
Note

Your Answer

(The main participants are the product, builder, optional director, and client. The builder creates the product and the client uses the builder, while the director can control the building steps. Before build() succeeds, the object is not a finished domain product because it has not passed all the required validation. This helps prevent incomplete or invalid locations from being saved.)

List at least three kinds of invalid configuration a location/zone build() should reject in this lab (name, zones, moisture thresholds). Why must those rules live in the domain builder, not only in the HTTP layer?
Note

Your Answer

(The builder should reject things like an empty or invalid location name, a location with no zones, and invalid moisture thresholds such as a minimum value being higher than the maximum. These rules should be in the domain builder because the domain should always protect itself, even if the data comes from somewhere other than the HTTP API.)

B. This phase of the application
What aggregate does the builder produce (location plus zones)? Why does this course use location_id (and never greenhouse_id) as the name for that scope?
Note

Your Answer

(The builder produces a complete location together with its zones. The application uses location_id because the domain calls these areas locations. greenhouse_id should not be used because that is not the name of this scope in the application.)

Describe the path from API request to persistence: DTO → builder steps → build() → repository. What must not be persisted if build() raises ConfigurationError (or equivalent)? Why does assigning a device wait until the zone row exists, and why does the client send only zone_id?
Note

Your Answer

(The API receives the DTO, passes the data to the builder, the builder adds the required parts, and build() checks that the configuration is valid. If ConfigurationError happens, nothing should be saved to the database. A device can only be assigned after the zone exists because the zone needs to have a database ID first. The client only sends zone_id because the server already knows which zone the device belongs to.)

Saving a location and its zones must be one transaction. What goes wrong if the location row commits and a later zone insert fails? How does that relate to “no half-built aggregates in the database”?
Note

Your Answer

(If the location is saved but one of the zone inserts fails, the database could contain a location without all its required zones. This creates an incomplete configuration. Using one transaction means everything is saved together, or everything is rolled back, so there are no half-built aggregates in the database.)

The configuration wizard UI collects fields in steps. How does that UI map to Builder without turning React (or the HTTP handler) into the place that owns domain validation?
Note

Your Answer

(The wizard can collect the information step by step and then send it to the API as a DTO. The API passes the data to the builder, which is responsible for the real domain validation. React can check simple things for user convenience, but it should not be the main place where the business rules are enforced.)

C. Compare, contrast, and scenarios
Contrast Builder with Factory Method and with Abstract Factory. Which pattern answers “which type?”, which answers “which matching kit?”, and which answers “how do we assemble one valid whole in steps?”
Note

Your Answer

(Factory Method mainly answers “which type of object should I create?” Abstract Factory answers “which matching group or kit of objects should I create?” Builder answers “how do I assemble one complete and valid object step by step?”)

Fluent method chaining (builder.add_zone(...).build()) is a coding style. Why is a fluent interface not the same thing as the Builder pattern?
Note

Your Answer

(Fluent chaining is just a way of writing methods so they can be called one after another. It does not automatically make the code a Builder pattern. Builder is about separating the step-by-step construction of a complex object from the final product and validating it before it is created.)

A classmate validates thresholds only in FastAPI / Pydantic and leaves build() empty. Another mutates builder fields after build() while treating the product as immutable. Explain why each is a trap.
Note

Your Answer

(The first approach is a trap because validation only in FastAPI means other parts of the application could create invalid configurations. The builder should also protect the domain rules. The second approach is a trap because once build() has created the product, it should be treated as complete and immutable. Changing the builder afterwards should not change the already-created product.)
