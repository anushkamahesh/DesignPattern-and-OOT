import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.domain.sensors.reading import Reading
from src.infrastructure.persistence.models import DeviceRow
from src.infrastructure.persistence.reading_repository import ReadingRepository
from src.infrastructure.persistence.session import get_db
from src.main import app

client = TestClient(app)


@pytest.fixture
def db():
    session = next(get_db())
    yield session
    session.close()


@pytest.fixture
def created(db):
    tracker = {"locations": [], "devices": []}
    yield tracker
    for lid in tracker["locations"]:
        client.delete(f"/api/locations/{lid}")
    db.expire_all()
    for did in tracker["devices"]:
        row = db.get(DeviceRow, uuid.UUID(did))
        if row is not None:
            db.delete(row)  # readings cascade
    db.commit()


def make_location(created, zone_count=2):
    zones = [
        {"name": f"Z{i}", "moisture_threshold_low": 0.3, "moisture_threshold_high": 0.6}
        for i in range(zone_count)
    ]
    r = client.post(
        "/api/locations/config",
        json={"location_name": f"Auto-{uuid.uuid4().hex[:8]}", "zones": zones},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    created["locations"].append(body["location"]["id"])
    return body


def seed_moisture(created, db, zone_id, value):
    s = client.post("/api/sensors", json={"type": "moisture"})
    assert s.status_code == 201
    device_id = s.json()["id"]
    created["devices"].append(device_id)
    # stop the background sampler from adding rows during the test
    client.patch(
        f"/api/devices/{device_id}/sampling",
        json={"sampling_interval_seconds": 300, "tracking_enabled": False},
    )
    assert client.patch(f"/api/devices/{device_id}/zone", json={"zone_id": zone_id}).status_code == 200
    ReadingRepository(db).insert(
        Reading(
            device_id=uuid.UUID(device_id),
            value=value,
            unit="vwc",
            source="simulation",
            recorded_at=datetime.now(timezone.utc),
        )
    )
    return device_id


def put(lid, key):
    return client.put(f"/api/locations/{lid}/automation", json={"strategy_key": key})


def test_strategies_endpoint_lists_known_keys():
    assert client.get("/api/automation/strategies").json() == ["aggressive", "conservative"]


def test_save_persists_and_get_returns_it(created):
    lid = make_location(created)["location"]["id"]
    assert client.get(f"/api/locations/{lid}/automation").json()["strategy_key"] is None
    assert put(lid, "conservative").status_code == 200
    assert put(lid, "aggressive").status_code == 200  # upsert, not a second row
    assert client.get(f"/api/locations/{lid}/automation").json()["strategy_key"] == "aggressive"


def test_unknown_key_is_400_and_missing_location_is_404(created):
    lid = make_location(created)["location"]["id"]
    assert put(lid, "nope").status_code == 400
    assert put(str(uuid.uuid4()), "conservative").status_code == 404
    assert client.post(f"/api/locations/{uuid.uuid4()}/automation/evaluate").status_code == 404


def test_evaluate_without_saved_strategy_is_400(created):
    lid = make_location(created)["location"]["id"]
    assert client.post(f"/api/locations/{lid}/automation/evaluate").status_code == 400


def test_evaluate_uses_persisted_key_and_zone_readings(created, db):
    body = make_location(created, zone_count=2)
    lid = body["location"]["id"]
    zone_with_sensor = body["zones"][0]["id"]
    seed_moisture(created, db, zone_with_sensor, 0.40)

    put(lid, "conservative")
    cons = {r["zone_id"]: r for r in client.post(f"/api/locations/{lid}/automation/evaluate").json()["recommendations"]}
    assert cons[zone_with_sensor]["action"] == "wait"

    put(lid, "aggressive")
    res = client.post(f"/api/locations/{lid}/automation/evaluate").json()
    assert res["strategy_key"] == "aggressive"
    agg = {r["zone_id"]: r for r in res["recommendations"]}
    assert agg[zone_with_sensor]["action"] == "irrigate"  # same moisture, different strategy


def test_zone_without_moisture_sensor_waits(created):
    body = make_location(created, zone_count=2)
    lid = body["location"]["id"]
    put(lid, "aggressive")
    recs = client.post(f"/api/locations/{lid}/automation/evaluate").json()["recommendations"]
    assert all(r["action"] == "wait" and "no moisture sensor" in r["reason"] for r in recs)


def test_unassigned_device_reading_is_not_borrowed(created, db):
    body = make_location(created, zone_count=1)
    lid = body["location"]["id"]
    s = client.post("/api/sensors", json={"type": "moisture"}).json()
    created["devices"].append(s["id"])
    client.patch(
        f"/api/devices/{s['id']}/sampling",
        json={"sampling_interval_seconds": 300, "tracking_enabled": False},
    )
    ReadingRepository(db).insert(
        Reading(uuid.UUID(s["id"]), 0.10, "vwc", "simulation", datetime.now(timezone.utc))
    )
    put(lid, "aggressive")
    rec = client.post(f"/api/locations/{lid}/automation/evaluate").json()["recommendations"][0]
    assert rec["action"] == "wait" and "no moisture sensor" in rec["reason"]