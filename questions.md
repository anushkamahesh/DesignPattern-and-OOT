A. Pattern

In your own words, what is a design pattern? What is it not?



A design pattern is a common way of solving a recurring software design problem. It gives developers an idea that can be adapted to their application. It is not something that must be used just because it exists.



Name the three GoF pattern families. For each family, give one-sentence: what kind of design problem it addresses. Then place Factory Method and Strategy into the correct family.



Creational- Deals with how objects are created and helps make object creation more flexible. Structural- Deals with how classes and objects are created connected and organised. and Behavioral- Deals with how objects communicates and shares responsibility.



A teammate wants to add a pattern “because it is on the course list,” even though the feature is small and unlikely to grow. When should you skip a pattern? What risk do you take if you apply one too early?



You should skip apattern when the feature is simple and not like to change and the pattern would make it complex. And using a pattern too early can make the code harder to understand and maintain. it can also create more classes and code than the actual feature needs.



B. This phase of the application

Why does Phase 1 ship a vertical slice that does almost no greenhouse business logic? What does “empty but running” prove that a folder of unimplemented classes would not?



Phase 1 is mainly about making sure the whole application works together. The backend, Postgrsql, alembic etc should all work. An empty but running application proves that these parts can communicate with each other.A folder containing unfinished classes would not prove that the actual application setup works.



List the four backend layer packages used in this course (domain, application, infrastructure, interfaces/api). For each, state what belongs there and give one example of something that must not live in domain.

Domain- Contains the main business rules and entities. It should not contain things like SQLAlchemy or FastAPI code.

Application- Contains the use cases and coordinates the work between different parts of the application.

infrastructure-Contains technical things such as database connections, settings, and external services.

and Interface/api-contains the API routes, request/response handling, and FastAPI.



What does GET /health return, and why does it check the database instead of only reporting that the HTTP process is up? Why is API documentation served at /scalar, and why is /docs disabled?



It checks the database because having the HTTP server running does not necessarily mean the application can communicate with PostgreSQL.The API documentation is available at /scalar because Scalar is used for the API documentation in this course. The default FastAPI /docs endpoint is disabled to follow the project requirements.



Phase 1 requires Alembic (or equivalent) with a baseline migration and no business tables such as devices. Why introduce the migration toolchain before any product schema? What would go wrong if you created tables by hand in Postgres and only added migrations later?



Alembic is introduced early so that database changes can be tracked from the beginning. The baseline migration gives the project a starting point. If we created tables manually in PostgreSQL and added migrations later the database and migration history could become different. This could cause problems when setting up the project on another computer or applying future database changes.



C. Compare, contrast, and scenarios

Explain dependency direction in this skeleton: which layers may import which? Why must domain code not import FastAPI, SQLAlchemy, or Pydantic models used as HTTP schemas?



The domain layer should stay independent. It should not import FastAPI, SQLAlchemy, or Pydantic HTTP models. This keeps the business logic independent from a specific web framework, database, or API technology.



The frontend cannot show a healthy badge. A classmate blames “the patterns.” What should you check first (stack, CORS/proxy, health JSON), and why is that a Phase 1 concern rather than a later pattern concern?



This is a Phase 1 problem because Phase 1 is about making sure the basic application stack can communicate. Design patterns are not the first thing to investigate when the frontend cannot reach the backend. What you have to check is, if the backend is running. Is the PostgreSQL running and if the Vite proxy pointing to the correct backend.



Course completion is at Phase 12, not Phase 1. What is still missing after a successful skeleton, and how do later phases add behaviour without rewriting the foundations you laid here?

Sensors, devices and readings, API endpoints and design pattern implementations. Phase 1 sets up the plumbing. Since the database, backend, and frontend are already connected, future phases can just add new features instead of rebuilding everything from scratch.

