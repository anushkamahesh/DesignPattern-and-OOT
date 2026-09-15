#questions.md

State the intent of Factory Method in plain language. What problem appears when callers scatter new / constructors (or a growing if type == ...) across the application?
Note

Your Answer

(Factory method is used to create objects without making the client decide exactly which class to create. It avoids having constructors or many if/elif statements scattered around the application. This makes the code easier to change and extend.)

Name the main participants of Factory Method (product, concrete product, creator, concrete creator, client). For each, give one sentence: what it is responsible for.
Note

Your Answer

(Product: Common type or interface that all created objects follow
Concrete product:The actual object that is created, such as a moisture sensor or light sensor.
Creator: Defines the method used to create a product.
Client: The part of the application that asks a creator to create a product.)

How do you add a new product variant when creators are polymorphic (new class + registry entry) versus when creation lives in one shared if/elif function? Why does that difference matter for extension?
Note

Your Answer

(With polymorphic creators we can change a new creator class and add it to the regisrty. We do not need to change the existing creators. With one big if/elif fuction, we have to modify the same fuctions every time we add a new type. The creator approach is better for extension because new types can be added with less change to exisitng code.)

B. This phase of the application
In this lab, what is the product and what are the concrete creators? Why must the API handler (or sensor service) go through a creator/registry instead of constructing MoistureSensor / LightSensor itself?
Note

Your Answer

(The product is the sensor objectThe concrete creators are MoistureSensorCreator and LightSensorCreato. The API handler or service should use the creator/registry because the creation logic belongs in the factory method. This keeps the API simple and prevents it from depending directly and specific sensor class.)

POST /api/sensors accepts a short type key such as "moisture" or "light", while the stored/returned field is device_type (for example moisture_sensor). Why are those two fields different? Who decides the stored device_type and default_config?
Note

Your Answer

(type is a shortkey sued by the client to choose which creator to use such as moisture or light. Device type is the actual type stored and returned for the device. The creator decided the stored device_type and the default_config. This means the client does not decide the sensor's default settings.)

Why is there a single devices table with role="sensor" instead of a dedicated sensors table? What later phase does that choice prepare for?
Note

Your Answer

(A single devices table allows different kinds of devices to be stored in one place.The role="sensor" value tells us that the device is a sensor.This prepares the project for Phase 3, where actuators can also be added to the same devices table.)

What should happen when the client posts an unknown type? Where should that rejection be decided (registry/service vs router constructing a concrete class anyway)?
Note

Your Answer

(The request should be rejected with a 400 Bad Request.The registry/service should check whether the requested type has a creator. If there is no creator, it should reject the request before anything is inserted into the database.)

C. Compare, contrast, and scenarios
Contrast Factory Method with a simple factory (one function full of if type == ...). When is the simple factory “good enough,” and why does this phase still want polymorphic creators?
Note

Your Answer

(A simple factory is usually one function with if/elif statements that decides which object to create.A simple factory is good enough when there are only a few types and the creation logic is very simple.This phase uses Factory Method because it separates the creation logic into different creator classes. This makes it easier to add new sensor types without changing one large function.)

Contrast Factory Method with Abstract Factory (Phase 3). Factory Method answers which question? Abstract Factory answers which different question? Why is Factory Method enough for Phase 2 sensors?
Note

Your Answer

(Factory Method is enough for Phase 2 because we only need to create individual sensors such as moisture and light sensors.

Abstract Factory is useful later when we need to create related groups or families of devices, such as sensors and actuators that belong together.)

A classmate puts SQLAlchemy session commits (or FastAPI request parsing) inside a concrete creator. Why is that a trap? Where should persistence and HTTP stay instead?
Note

Your Answer

(A creator should only be responsible for creating the domain object.If SQLAlchemy commits or FastAPI request handling is put inside the creator, the creator becomes tightly connected to the database or HTTP layer. This makes the code harder to test and maintain.HTTP handling should stay in the API/router, and database persistence should stay in the repository/infrastructure layer.)