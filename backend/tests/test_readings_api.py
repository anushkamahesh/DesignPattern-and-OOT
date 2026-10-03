import uuid

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_read_inserts_row_and_returns_normalized_dto():
    s = client.post("/api/sensors", json={"type": "moisture"})
    device_id = s.json()["id"]

    r = client.post(f"/api/sensors/{device_id}/read")
    assert r.status_code == 201
    body = r.json()
    assert body["device_id"] == device_id
    assert body["source"] == "simulation"
    assert 0.2 <= body["value"] <= 0.6

    hist = client.get(f"/api/sensors/{device_id}/readings?limit=10")
    assert hist.status_code == 200
    assert len(hist.json()) >= 1


def test_repeated_reads_increase_row_count():
    s = client.post("/api/sensors", json={"type": "moisture"})
    device_id = s.json()["id"]
    client.post(f"/api/sensors/{device_id}/read")
    client.post(f"/api/sensors/{device_id}/read")
    hist = client.get(f"/api/sensors/{device_id}/readings?limit=10").json()
    assert len(hist) == 2


def test_read_missing_device_is_404():
    r = client.post(f"/api/sensors/{uuid.uuid4()}/read")
    assert r.status_code == 404


def test_sampling_patch_persists_values():
    s = client.post("/api/sensors", json={"type": "moisture"})
    device_id = s.json()["id"]
    r = client.patch(
        f"/api/devices/{device_id}/sampling",
        json={"sampling_interval_seconds": 60, "tracking_enabled": False},
    )
    assert r.status_code == 200
    assert r.json()["sampling_interval_seconds"] == 60
    assert r.json()["tracking_enabled"] is False


def test_sampling_patch_rejects_small_interval():
    s = client.post("/api/sensors", json={"type": "moisture"})
    device_id = s.json()["id"]
    r = client.patch(
        f"/api/devices/{device_id}/sampling",
        json={"sampling_interval_seconds": 2, "tracking_enabled": True},
    )
    assert r.status_code == 400