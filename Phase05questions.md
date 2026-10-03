Phase 5 — Adapter questions
Pattern / focus: Adapter.

Read first: Guide 05 · Requirements

How to answer
Use your own wording. Do not paste teaching-example types (for example a legacy XML calendar client) as if they were your greenhouse classes.
When a question asks about this application, refer to sensor ports, adapters, readings, and sensor_readings from the lab.
Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
Write each answer inside the matching Your Answer note. Replace the placeholder; leave the question text unchanged.
A. Pattern
State the intent of Adapter in plain language. What problem appears when business code speaks a vendor or legacy protocol (odd field names, units, XML, status codes) directly?
Note

Your Answer

(The purpose of Adapter is to make an existing system work with another interface. Without an adapter, the business code would need to understand vendor-specific field names, units, XML formats, or status codes. The adapter translates these differences into a format the application already understands.)

Name the participants (target / port, adaptee, adapter, client). What does the adapter translate, and what must it not decide (business policy)?
Note

Your Answer

(The target/port is the interface the application expects. The adaptee is the existing vendor or legacy system with a different interface. The adapter connects them and translates the data, while the client uses the target/port. The adapter should only translate the data and should not make business decisions or policies.)

GoF distinguishes an object adapter (composition) from a class adapter (inheritance). Which does modern code prefer, and why?
Note

Your Answer

(Modern code usually prefers an object adapter because it uses composition instead of inheritance. This makes the code more flexible and allows us to change or replace the adapted object more easily.)

B. This phase of the application
What is SensorPort in this lab, and what normalized value type (for example Reading) do adapters return? Why do application services depend on the port rather than on a simulation driver or vendor SDK?
Note

Your Answer

(SensorPort is the common interface that the application uses to get sensor readings. The adapters return a normalized value such as Reading. Application services depend on the port so they do not need to know which simulation driver, vendor SDK, or other sensor system is being used.)

You need three translations onto the same normalized reading: a simulation adapter, a vendor stub, and an MQTT translator that accepts a payload dict. Why is the different raw shape the point of the exercise? How does source (simulation, vendor, or mqtt) show which adapter produced the reading, and why must the MQTT translator not open a broker in this phase? Phase 12 may deliver that same dict on a device HTTP route or through an optional broker — why must this phase still not open either transport?
Note

Your Answer

(The different raw shapes show why an adapter is needed. The simulation, vendor stub, and MQTT data can all look different, but their adapters convert them into the same Reading format. The source value shows whether the reading came from simulation, vendor, or mqtt. The MQTT translator should not open a broker because this phase is only about translating the data, not handling the transport. Phase 12 can handle HTTP or an optional broker later, so this phase should keep the adapter simple and focused on translation.)

Readings are appended to sensor_readings (history grows). Why not keep only the latest value in memory or overwrite a single row, and which later phase consumes this history? Why do a manual read, the simulation sampler, and (later) MQTT share one writer of that table? Why does the sampler skip devices with tracking off and MQTT devices, and why do sensor cards poll the latest stored reading until Phase 12?
Note

Your Answer

(Readings are appended so the application keeps a history instead of only knowing the latest value. This history is used later by Phase 12. Manual reads, the simulation sampler, and later MQTT should use one writer so that readings are stored consistently. The sampler skips devices with tracking turned off and MQTT devices because those devices should not be sampled by the simulation. Until Phase 12, sensor cards poll the latest stored reading so they can show the current value without needing a live sensor connection.)

POST /api/sensors/{id}/read runs an adapter, persists, and returns a DTO. What HTTP status is appropriate when the device is missing versus when the adapter fails? Why must the router never see vendor-shaped types?
Note

Your Answer

(If the device is missing, the API should return 404 Not Found. If the adapter fails while trying to get a reading, it should return an appropriate 5xx error, such as 500 Internal Server Error. The router should only work with the application's normal data types and should not need to understand vendor-specific types.)

C. Compare, contrast, and scenarios
Contrast Adapter with Facade. Adapter changes the shape of an existing interface; Facade simplifies how to use a subsystem. Give a greenhouse-shaped example of each (Adapter this phase; Facade in Phase 7).
Note

Your Answer

(An Adapter changes the shape of an existing interface so it can be used by the application. For example, a vendor sensor may return temperature in a different format, and the adapter converts it into the application's Reading. A Facade provides a simpler way to use a more complicated subsystem. For example, a greenhouse facade in Phase 7 could provide one simple method for managing several greenhouse operations without the user needing to know all the internal steps.)

Contrast Adapter with Decorator. Both wrap an object. What is different about the interface they present to the client?
Note

Your Answer

(An Adapter wraps an object and gives the client the interface it expects. A Decorator keeps the same interface but adds extra behaviour to the object. For example, an adapter could convert a vendor sensor format into Reading, while a decorator could add logging to a sensor without changing how the sensor is used.)

A classmate puts irrigation policy (“if moisture < 0.3 then water”) inside the vendor adapter. Why is that a trap? Where should that decision live instead (later Strategy), and what should stay in the adapter?
Note

Your Answer

(Putting irrigation rules inside the vendor adapter is a problem because the adapter should only translate the vendor data. It should not decide when the greenhouse should water plants. That decision should be handled later by a Strategy, where the irrigation policy can be changed without changing the adapter. The adapter should only translate the vendor's raw reading into the application's normal Reading format.)
