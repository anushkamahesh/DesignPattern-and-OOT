import uuid

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.persistence.models import DeviceRow
from src.infrastructure.persistence.session import get_db
from src.main import app

client = TestClient(app)


def _name(prefix="T"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _zone(name, low=0.2, high=0.6):
    return {"name": name, "moisture_threshold_low": low, "moisture_threshold_high": high}


@pytest.fixture
def db():
    gen = get_db()
    session = next(gen)
    yield session
    session.close()


@pytest.fixture
def created(db):
    """Tracks locations and devices created by a test and removes them afterwards."""
    tracker = {"locations": [], "devices": []}
    yield tracker
    for lid in tracker["locations"]:
        client.delete(f"/api/locations/{lid}")
    db.expire_all()
    for did in tracker["devices"]:
        row = db.get(DeviceRow, uuid.UUID(did))
        if row is not None:
            db.delete(row)
    db.commit()


def make_location(created, zones=None):
    zones = zones or [_zone("Zone A"), _zone("Zone B", 0.3, 0.7)]
    r = client.post("/api/locations/config", json={"location_name": _name("Loc"), "zones": zones})
    assert r.status_code == 201, r.text
    body = r.json()
    created["locations"].append(body["location"]["id"])
    return body


def make_device(created):
    r = client.post("/api/sensors", json={"type": "moisture"})
    assert r.status_code == 201, r.text
    did = r.json()["id"]
    created["devices"].append(did)
    return did


def assign(device_id, zone_id):
    return client.patch(f"/api/devices/{device_id}/zone", json={"zone_id": zone_id})


def device_row(db, device_id):
    db.expire_all()
    return db.get(DeviceRow, uuid.UUID(device_id))


# ---- create / read ----
def test_create_persists_location_and_zones(created):
    body = make_location(created)
    lid = body["location"]["id"]
    assert len(body["zones"]) == 2
    assert all(z["location_id"] == lid for z in body["zones"])


def test_get_config_returns_structure_with_location_id(created):
    body = make_location(created)
    lid = body["location"]["id"]
    r = client.get(f"/api/locations/{lid}/config")
    assert r.status_code == 200
    data = r.json()
    assert data["location"]["id"] == lid
    assert {z["name"] for z in data["zones"]} == {"Zone A", "Zone B"}
    assert all(z["location_id"] == lid for z in data["zones"])


def test_get_missing_location_is_404():
    assert client.get(f"/api/locations/{uuid.uuid4()}/config").status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"location_name": "X", "zones": []},
        {"location_name": " ", "zones": [_zone("Z")]},
        {"location_name": "X", "zones": [_zone("Z", 0.8, 0.2)]},
        {"location_name": "X", "zones": [_zone("Z", 0.1, 1.5)]},
        {"location_name": "X", "zones": [_zone("Z"), _zone("z")]},
    ],
)
def test_invalid_payload_is_400(payload):
    r = client.post("/api/locations/config", json=payload)
    assert r.status_code == 400
    assert r.json()["detail"]


def test_invalid_create_writes_nothing():
    before = len(client.get("/api/locations").json())
    client.post("/api/locations/config", json={"location_name": "X", "zones": []})
    assert len(client.get("/api/locations").json()) == before


# ---- list / delete ----
def test_list_returns_every_created_location(created):
    a = make_location(created)["location"]["id"]
    b = make_location(created)["location"]["id"]
    ids = [x["id"] for x in client.get("/api/locations").json()]
    assert a in ids and b in ids
    assert ids.index(b) < ids.index(a)  # newest first


def test_delete_location_removes_it_and_keeps_the_other(created):
    a = make_location(created)
    b = make_location(created)
    aid, bid = a["location"]["id"], b["location"]["id"]
    assert client.delete(f"/api/locations/{aid}").status_code == 204
    assert client.get(f"/api/locations/{aid}/config").status_code == 404
    assert client.get(f"/api/locations/{bid}/config").status_code == 200
    assert client.delete(f"/api/locations/{aid}").status_code == 404


def test_delete_location_unassigns_devices_but_keeps_them(created, db):
    body = make_location(created)
    device = make_device(created)
    assert assign(device, body["zones"][0]["id"]).status_code == 200
    client.delete(f"/api/locations/{body['location']['id']}")
    row = device_row(db, device)
    assert row is not None
    assert row.zone_id is None and row.location_id is None


# ---- assignment ----
def test_assign_two_devices_zone_list_has_only_those(created):
    body = make_location(created)
    lid = body["location"]["id"]
    z1, z2 = body["zones"][0]["id"], body["zones"][1]["id"]
    d1, d2, d3, d4 = (make_device(created) for _ in range(4))
    assert assign(d1, z2).status_code == 200
    assert assign(d2, z2).status_code == 200
    assert assign(d3, z1).status_code == 200  # another zone; d4 stays unassigned
    r = client.get(f"/api/locations/{lid}/zones/{z2}/devices")
    assert r.status_code == 200
    ids = {d["id"] for d in r.json()}
    assert ids == {d1, d2}
    assert d3 not in ids and d4 not in ids


def test_assign_copies_location_id_from_zone(created):
    body = make_location(created)
    d = make_device(created)
    r = assign(d, body["zones"][0]["id"])
    assert r.json()["location_id"] == body["location"]["id"]


def test_unassign_clears_zone_id_and_location_id(created, db):
    body = make_location(created)
    d = make_device(created)
    assign(d, body["zones"][0]["id"])
    r = assign(d, None)
    assert r.status_code == 200
    assert r.json()["zone_id"] is None and r.json()["location_id"] is None
    row = device_row(db, d)
    assert row.zone_id is None and row.location_id is None


def test_assign_missing_device_or_zone_is_404(created):
    body = make_location(created)
    d = make_device(created)
    assert assign(str(uuid.uuid4()), body["zones"][0]["id"]).status_code == 404
    assert assign(d, str(uuid.uuid4())).status_code == 404


def test_zone_device_list_404_for_wrong_location(created):
    a = make_location(created)
    b = make_location(created)
    r = client.get(f"/api/locations/{b['location']['id']}/zones/{a['zones'][0]['id']}/devices")
    assert r.status_code == 404


# ---- zone management ----
def test_add_zone_persists_on_existing_location(created):
    body = make_location(created)
    lid = body["location"]["id"]
    r = client.post(f"/api/locations/{lid}/zones", json=_zone("Zone C", 0.1, 0.5))
    assert r.status_code == 201
    assert r.json()["location_id"] == lid
    cfg = client.get(f"/api/locations/{lid}/config").json()
    assert "Zone C" in {z["name"] for z in cfg["zones"]}


def test_add_zone_to_missing_location_is_404():
    r = client.post(f"/api/locations/{uuid.uuid4()}/zones", json=_zone("Z"))
    assert r.status_code == 404


def test_invalid_zone_update_is_400_and_changes_nothing(created):
    body = make_location(created)
    lid, zid = body["location"]["id"], body["zones"][0]["id"]
    r = client.patch(
        f"/api/locations/{lid}/zones/{zid}",
        json={"moisture_threshold_low": 0.9, "moisture_threshold_high": 0.1},
    )
    assert r.status_code == 400
    cfg = client.get(f"/api/locations/{lid}/config").json()
    zone = next(z for z in cfg["zones"] if z["id"] == zid)
    assert zone["moisture_threshold_low"] == 0.2 and zone["moisture_threshold_high"] == 0.6


def test_valid_zone_update(created):
    body = make_location(created)
    lid, zid = body["location"]["id"], body["zones"][0]["id"]
    r = client.patch(
        f"/api/locations/{lid}/zones/{zid}",
        json={"name": "Renamed", "schedule": {"start": "07:00"}},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"
    assert r.json()["schedule"] == {"start": "07:00"}


def test_delete_zone_unassigns_its_devices(created, db):
    body = make_location(created)
    lid, zid = body["location"]["id"], body["zones"][0]["id"]
    d = make_device(created)
    assign(d, zid)
    assert client.delete(f"/api/locations/{lid}/zones/{zid}").status_code == 204
    row = device_row(db, d)
    assert row is not None and row.zone_id is None and row.location_id is None
    cfg = client.get(f"/api/locations/{lid}/config").json()
    assert zid not in {z["id"] for z in cfg["zones"]}


def test_delete_last_zone_is_400_and_zone_stays(created):
    body = make_location(created, zones=[_zone("Only")])
    lid, zid = body["location"]["id"], body["zones"][0]["id"]
    assert client.delete(f"/api/locations/{lid}/zones/{zid}").status_code == 400
    cfg = client.get(f"/api/locations/{lid}/config").json()
    assert [z["id"] for z in cfg["zones"]] == [zid]


def test_delete_zone_from_wrong_location_is_404(created):
    a = make_location(created)
    b = make_location(created)
    r = client.delete(f"/api/locations/{b['location']['id']}/zones/{a['zones'][0]['id']}")
    assert r.status_code == 404