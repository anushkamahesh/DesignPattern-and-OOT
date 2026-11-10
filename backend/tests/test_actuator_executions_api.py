import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from src.infrastructure.persistence.models import (
    ActuatorExecutionLogRow,
    ActuatorStateRow,
    DeviceRow,
)
from src.infrastructure.persistence.session import get_db
from src.main import app

client = TestClient(app)


@pytest.fixture
def db():
    session = next(get_db())
    yield session
    session.close()


@pytest.fixture
def actuator(db):
    row = DeviceRow(
        device_type="pump",
        role="actuator",
        display_name=f"Pump-{uuid.uuid4().hex[:6]}",
        default_config={},
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    device_id = str(row.id)
    yield device_id
    db.expire_all()
    leftover = db.get(DeviceRow, uuid.UUID(device_id))
    if leftover is not None:
        db.delete(leftover)  # state and execution rows cascade
        db.commit()


def apply(device_id, command="start_pump"):
    return client.post(f"/api/actuators/{device_id}/apply", json={"command": command})


def go(device_id, target):
    return client.post(f"/api/devices/{device_id}/transition", json={"target": target})


def log_rows(db, device_id):
    db.expire_all()
    return db.scalars(
        select(ActuatorExecutionLogRow)
        .where(ActuatorExecutionLogRow.device_id == uuid.UUID(device_id))
        .order_by(ActuatorExecutionLogRow.created_at)
    ).all()


def age_state(db, device_id, minutes):
    row = db.get(ActuatorStateRow, uuid.UUID(device_id))
    row.updated_at = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    db.commit()


def test_successful_apply_writes_a_log_row(actuator, db):
    r = apply(actuator)
    assert r.status_code == 201
    body = r.json()
    assert body["device_id"] == actuator
    assert body["success"] is True
    assert body["policy_applied"] == ["logging"]
    assert body["message"] is None
    rows = log_rows(db, actuator)
    assert len(rows) == 1 and rows[0].success is True


def test_unknown_command_still_succeeds(actuator):
    r = apply(actuator, "banana")
    assert r.status_code == 201
    assert r.json()["success"] is True


def test_running_a_short_time_is_not_blocked(actuator):
    assert go(actuator, "running").status_code == 200
    assert apply(actuator, "stop_pump").status_code == 201


def test_blocked_attempt_is_409_and_logged_as_a_failure(actuator, db):
    assert go(actuator, "running").status_code == 200
    age_state(db, actuator, 31)

    r = apply(actuator, "stop_pump")
    assert r.status_code == 409
    assert r.json()["detail"] == "Max run time exceeded"

    rows = log_rows(db, actuator)
    assert len(rows) == 1
    assert rows[0].success is False
    assert rows[0].policy_applied == ["maxRunTime", "logging"]
    assert rows[0].message == "Max run time exceeded"

    listed = client.get("/api/actuators/executions?limit=5").json()
    mine = next(x for x in listed if x["device_id"] == actuator)
    assert mine["success"] is False
    assert mine["policy_applied"] == ["maxRunTime", "logging"]
    assert mine["message"] == "Max run time exceeded"


def test_transitioning_out_of_running_resets_the_clock(actuator, db):
    assert go(actuator, "running").status_code == 200
    age_state(db, actuator, 31)
    assert apply(actuator).status_code == 409
    assert go(actuator, "idle").status_code == 200
    assert go(actuator, "running").status_code == 200  # updated_at is fresh again
    assert apply(actuator).status_code == 201


def test_missing_actuator_is_404_and_writes_no_row(db):
    before = len(client.get("/api/actuators/executions?limit=200").json())
    assert apply(uuid.uuid4()).status_code == 404
    assert len(client.get("/api/actuators/executions?limit=200").json()) == before


def test_a_sensor_is_not_an_actuator(db):
    s = client.post("/api/sensors", json={"type": "moisture"}).json()
    try:
        assert apply(s["id"]).status_code == 404
    finally:
        row = db.get(DeviceRow, uuid.UUID(s["id"]))
        if row is not None:
            db.delete(row)
            db.commit()


def test_executions_route_is_not_shadowed_by_the_id_route():
    r = client.get("/api/actuators/executions")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_executions_are_newest_first_and_respect_the_limit(actuator):
    for command in ("a", "b", "c"):
        assert apply(actuator, command).status_code == 201
    items = client.get("/api/actuators/executions?limit=2").json()
    assert len(items) == 2
    assert all(i["device_id"] == actuator for i in items)
    assert items[0]["created_at"] >= items[1]["created_at"]
    assert client.get("/api/actuators/executions?limit=0").status_code == 422