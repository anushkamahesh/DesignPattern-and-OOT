import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from src.application.automation.dto import ZoneRecommendationResponse
from src.application.overview.facade import summarize_recommendations
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


def add_reading(db, device_id, value, recorded_at):
    ReadingRepository(db).insert(
        Reading(
            device_id=uuid.UUID(device_id),
            value=value,
            unit="vwc",
            source="simulation",
            recorded_at=recorded_at,
        )
    )


def make_sensor(created, name, tracking=False, interval=120):
    s = client.post("/api/sensors", json={"type": "moisture", "display_name": name})
    assert s.status_code == 201, s.text
    sid = s.json()["id"]
    created["devices"].append(sid)
    client.patch(
        f"/api/devices/{sid}/sampling",
        json={"sampling_interval_seconds": interval, "tracking_enabled": tracking},
    )
    return sid


@pytest.fixture
def seeded(created, db):
    """Location with Zone A and Zone B (empty). Zone A holds an assigned sensor
    (older reading 0.55, newest 0.40) and an assigned actuator with no reading.
    A separate unassigned sensor also has a reading."""
    name = f"Overview-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/locations/config",
        json={
            "location_name": name,
            "zones": [
                {"name": "Zone A", "moisture_threshold_low": 0.3, "moisture_threshold_high": 0.6},
                {"name": "Zone B", "moisture_threshold_low": 0.3, "moisture_threshold_high": 0.6},
            ],
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    lid = body["location"]["id"]
    created["locations"].append(lid)
    zone_a = next(z["id"] for z in body["zones"] if z["name"] == "Zone A")

    sensor_id = make_sensor(created, "Assigned moisture")
    assert client.patch(f"/api/devices/{sensor_id}/zone", json={"zone_id": zone_a}).status_code == 200
    now = datetime.now(timezone.utc)
    add_reading(db, sensor_id, 0.55, now - timedelta(minutes=10))
    add_reading(db, sensor_id, 0.40, now)

    actuator = DeviceRow(
        device_type="pump",
        role="actuator",
        display_name="Zone A pump",
        default_config={},
        zone_id=uuid.UUID(zone_a),
        location_id=uuid.UUID(lid),
    )
    db.add(actuator)
    db.commit()
    db.refresh(actuator)
    created["devices"].append(str(actuator.id))

    unassigned_id = make_sensor(created, "Unassigned moisture")
    add_reading(db, unassigned_id, 0.10, now)

    return {
        "lid": lid,
        "name": name,
        "sensor_id": sensor_id,
        "actuator_id": str(actuator.id),
        "unassigned_id": unassigned_id,
    }


def overview(lid):
    return client.get(f"/api/locations/{lid}/overview")


def put(lid, key):
    return client.put(f"/api/locations/{lid}/automation", json={"strategy_key": key})


def test_overview_unknown_location_is_404():
    assert overview(uuid.uuid4()).status_code == 404


def test_overview_returns_strategy_and_readings(seeded):
    s = seeded
    lid = s["lid"]

    r = overview(lid)
    assert r.status_code == 200
    body = r.json()
    assert body["location"]["id"] == lid
    assert body["location"]["name"] == s["name"]

    # no key saved yet: still 200, both fields null
    assert body["strategy_key"] is None
    assert body["last_recommendation"] is None

    # only assigned devices are counted
    assert body["device_counts"] == {"sensor": 1, "actuator": 1}

    zones = {z["name"]: z for z in body["zones"]}
    assert set(zones) == {"Zone A", "Zone B"}

    # unassigned device appears nowhere
    listed = [d["id"] for z in body["zones"] for d in z["devices"]]
    read = [x["device_id"] for z in body["zones"] for x in z["latest_readings"]]
    assert s["unassigned_id"] not in listed
    assert s["unassigned_id"] not in read

    za = zones["Zone A"]
    assert za["moisture_threshold_low"] == pytest.approx(0.3)
    assert za["moisture_threshold_high"] == pytest.approx(0.6)
    assert {d["id"] for d in za["devices"]} == {s["sensor_id"], s["actuator_id"]}

    # one newest reading, only for the device that has one; device fields copied on
    assert [x["device_id"] for x in za["latest_readings"]] == [s["sensor_id"]]
    reading = za["latest_readings"][0]
    assert reading["value"] == pytest.approx(0.40)
    assert reading["unit"] == "vwc"
    assert reading["tracking_enabled"] is False
    assert reading["sampling_interval_seconds"] == 120
    assert reading["recorded_at"]

    # the zone with no assigned devices is still listed, and empty
    assert zones["Zone B"]["devices"] == []
    assert zones["Zone B"]["latest_readings"] == []

    # after saving a key, last_recommendation matches evaluate for this location
    assert put(lid, "aggressive").status_code == 200
    body = overview(lid).json()
    assert body["strategy_key"] == "aggressive"
    ev = client.post(f"/api/locations/{lid}/automation/evaluate").json()["recommendations"]
    irrigating = [r for r in ev if r["action"] == "irrigate"]
    last = body["last_recommendation"]
    assert last["action"] == ("irrigate" if irrigating else "wait")
    for r in irrigating or ev:
        assert r["reason"] in last["reason"]


def test_overview_reflects_database_changes(seeded, db):
    s = seeded
    lid = s["lid"]

    put(lid, "aggressive")  # 0.40 is below the midpoint 0.45
    assert overview(lid).json()["last_recommendation"]["action"] == "irrigate"

    put(lid, "conservative")  # 0.40 is not below the low threshold 0.30
    body = overview(lid).json()
    assert body["strategy_key"] == "conservative"
    assert body["last_recommendation"]["action"] == "wait"

    add_reading(db, s["sensor_id"], 0.20, datetime.now(timezone.utc) + timedelta(seconds=1))
    body = overview(lid).json()
    zone_a = next(z for z in body["zones"] if z["name"] == "Zone A")
    assert zone_a["latest_readings"][0]["value"] == pytest.approx(0.20)
    assert body["last_recommendation"]["action"] == "irrigate"


def rec(zone, action, reason):
    return ZoneRecommendationResponse(
        zone_id=uuid.uuid4(), zone_name=zone, action=action, reason=reason
    )


def test_summary_irrigates_when_any_zone_irrigates():
    s = summarize_recommendations([rec("A", "wait", "moist enough"), rec("B", "irrigate", "too dry")])
    assert s.action == "irrigate"
    assert "B: too dry" in s.reason
    assert "moist enough" not in s.reason


def test_summary_waits_when_every_zone_waits():
    s = summarize_recommendations([rec("A", "wait", "ok"), rec("B", "wait", "no moisture sensor in this zone")])
    assert s.action == "wait"
    assert "A: ok" in s.reason and "B: no moisture sensor in this zone" in s.reason