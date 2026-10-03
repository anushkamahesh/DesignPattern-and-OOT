import uuid
from datetime import datetime, timedelta, timezone
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from src.application.readings.service import ReadingIngest
from src.application.readings.sampler import SimulationSampler
from src.infrastructure.persistence.reading_repository import ReadingRepository
from src.infrastructure.persistence.session import get_db
from src.main import app

client = TestClient(app)


def _make_device():
    r = client.post("/api/sensors", json={"type": "moisture"})
    assert r.status_code == 201
    return r.json()["id"]


def test_sampler_inserts_on_elapsed_interval_and_skips_within_it():
    device_id = _make_device()
    client.patch(
        f"/api/devices/{device_id}/sampling",
        json={"sampling_interval_seconds": 5, "tracking_enabled": True},
    )

    db = next(get_db())
    repo = ReadingRepository(db)
    sampler = SimulationSampler(repo, ReadingIngest(repo))

    def count_for_device():
        return len(repo.list_recent(uuid.UUID(device_id), limit=100))

    t0 = datetime.now(timezone.utc)
    sampler.run_once(t0)
    assert count_for_device() == 1

    sampler.run_once(t0 + timedelta(seconds=1))
    assert count_for_device() == 1  # unchanged: interval has not elapsed

    sampler.run_once(t0 + timedelta(seconds=6))
    assert count_for_device() == 2  # one more: interval has elapsed
    db.close()


def test_sampler_skips_tracking_disabled_devices():
    device_id = _make_device()
    client.patch(
        f"/api/devices/{device_id}/sampling",
        json={"sampling_interval_seconds": 5, "tracking_enabled": False},
    )

    db = next(get_db())
    repo = ReadingRepository(db)
    sampler = SimulationSampler(repo, ReadingIngest(repo))
    sampler.run_once(datetime.now(timezone.utc))
    assert len(repo.list_recent(uuid.UUID(device_id), limit=10)) == 0
    db.close()


def test_sampler_skips_mqtt_devices():
    r = client.post("/api/sensors", json={"type": "moisture"})
    device_id = r.json()["id"]

    db = next(get_db())
    from src.infrastructure.persistence.models import DeviceRow

    row = db.get(DeviceRow, uuid.UUID(device_id))
    row.default_config = {**(row.default_config or {}), "protocol": "mqtt"}
    row.sampling_interval_seconds = 5
    row.tracking_enabled = True
    db.commit()

    repo = ReadingRepository(db)
    sampler = SimulationSampler(repo, ReadingIngest(repo))
    sampler.run_once(datetime.now(timezone.utc))
    assert len(repo.list_recent(uuid.UUID(device_id), limit=10)) == 0
    db.close()