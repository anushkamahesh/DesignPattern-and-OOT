import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.application.readings.sampler import SimulationSampler
from src.application.readings.service import ReadingIngest
from src.infrastructure.persistence.reading_repository import ReadingRepository
from src.infrastructure.persistence.session import SessionLocal
from src.interfaces.api.devices import router as devices_router
from src.interfaces.api.locations import router as locations_router
from src.interfaces.api.sensors import router as sensors_router

# How often the background sampler checks for devices whose interval has
# elapsed. Each device is still only sampled on its own
# sampling_interval_seconds; this is just the tick rate of the check.
SAMPLER_TICK_SECONDS = 5


async def _sampler_loop() -> None:
    while True:
        await asyncio.sleep(SAMPLER_TICK_SECONDS)
        db = SessionLocal()
        try:
            repo = ReadingRepository(db)
            sampler = SimulationSampler(repo, ReadingIngest(repo))
            sampler.run_once(datetime.now(timezone.utc))
        except Exception:
            db.rollback()
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_sampler_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="Smart Greenhouse API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sensors_router)
app.include_router(locations_router)
app.include_router(devices_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def read_root():
    return {"message": "Smart Greenhouse API is running"}