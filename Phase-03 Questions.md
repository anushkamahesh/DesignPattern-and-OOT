# Phase 3 — Abstract Factory questions

**Pattern / focus:** Abstract Factory.

**Read first:** [Guide 03](../../materials/guides/03-abstract-factory.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example warrior/mage class kits) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to device families, provision, and the unified devices API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Abstract Factory in plain language. What goes wrong when related products are chosen independently (`if format` for each piece) instead of as a **family**?

> [!NOTE]
> ***Your Answer***
>
> _(Abstract Factory is used to create a group of related objects that are meant to work together. If each product is chosen separately with different if format checks, it is easy to accidentally combine products from different families. Using a factory keeps the whole family consistent.)_

2. Name the main participants (**abstract factory**, **concrete factory**, **abstract products**, **concrete products**, **client**). How does choosing a factory at the start **commit** the client to one family?

> [!NOTE]
> ***Your Answer***
>
> _(The main participants are the abstract factory, concrete factory, abstract products, concrete products, and the client. The client chooses a concrete factory at the beginning, and that factory decides which concrete products are created. This means the client stays with one compatible product family instead of mixing different families.)_

3. When should you use Abstract Factory, and when should you skip it (for example only one product type per request, or mixing siblings is valid)?

> [!NOTE]
> ***Your Answer***
>
> _(Abstract Factory should be used when several related products need to be created together and they should belong to the same family. It can be skipped when there is only one product type to create or when mixing different product families is completely valid.)_

## B. This phase of the application

4. In this lab, what is a **device family**, and what does `create_device_set()` (or your equivalent) return? Why must a simulation kit and an edge kit not mix incompatible siblings?

> [!NOTE]
> ***Your Answer***
>
> _(A device family is a group of compatible devices that are designed to work together, such as the simulation family or edge family. create_device_set() returns a complete device kit containing the devices needed for that family. A simulation kit and an edge kit should not be mixed because their devices may have different behaviour or requirements.)_

5. Phase 2 Factory Method creators still exist. How does Abstract Factory **compose** them rather than replace them? What would you lose if you deleted the sensor creators and inlined all construction inside the family factory?

> [!NOTE]
> ***Your Answer***
>
> _(Abstract Factory uses the Phase 2 Factory Method creators inside the family factory. The family factory decides which family is needed, while the existing sensor creators still handle the creation of individual sensors. If we deleted them and put everything inside the family factory, we would lose the separation of responsibilities and make the family factory much harder to maintain.)_

6. Why add a `device_family` column on the existing `devices` table (with a default/backfill such as `"simulation"`) instead of a new table per family? What happens to Phase 2 sensor rows if you forget the backfill?

> [!NOTE]
> ***Your Answer***
>
> _(Adding a device_family column keeps the existing devices table and lets each device be identified by its family. Creating a separate table for every family would make the database more complicated and duplicate similar information. The existing Phase 2 sensor rows need to be backfilled with something like "simulation"; otherwise, they may have a missing family and filtering or other application logic may not handle them correctly.)_

7. `POST /api/devices/provision` returns a kit (expected size: two sensors and two actuators). `GET /api/devices` can filter by `family` and `role`. Why must the UI be able to filter by family? Why do `/api/sensors` routes from Phase 2 still need to work?

> [!NOTE]
> ***Your Answer***
>
> _(The UI needs to filter by family so users can see the correct group of devices, for example simulation devices separately from edge devices. This is especially important when different families can contain similar device roles. The /api/sensors routes must still work because existing Phase 2 functionality should not break when the new Abstract Factory features are added.)_

## C. Compare, contrast, and scenarios

8. Draw the contrast in one paragraph: Factory Method vs Abstract Factory. Use the questions “which **one** product?” versus “which product **line**?” and mention that Abstract Factory often **uses** Factory Method–style methods inside.

> [!NOTE]
> ***Your Answer***
>
> _(Factory Method mainly answers “which one product should I create?”, while Abstract Factory answers “which product line or family should I use?” Factory Method is useful for creating an individual product, while Abstract Factory creates a group of related products that belong together. Abstract Factory can also use Factory Method–style methods inside it to create the individual products in the family.)_

9. A DTO or HTTP handler constructs concrete simulation/edge device types directly, bypassing the family factory. What consistency bug can that reintroduce? How should HTTP stay on the abstract factory / service instead?

> [!NOTE]
> ***Your Answer***
>
> _(If a DTO or HTTP handler creates a concrete simulation or edge device directly, it could accidentally mix devices from different families. This would bring back the consistency problem that Abstract Factory is supposed to prevent. The HTTP layer should instead call the service or abstract factory, which chooses the correct family and creates the compatible devices.)_

10. Someone proposes a single “god factory” that creates locations, readings, and devices “because we already have a factory.” Why is that a misuse of Abstract Factory?

> [!NOTE]
> ***Your Answer***
>
> _(Write your answer here.)_
