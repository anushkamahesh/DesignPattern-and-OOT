from datetime import datetime, timezone
from uuid import uuid4

from src.infrastructure.adapters.sensors.mqtt import MqttSensorAdapter
from src.infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from src.infrastructure.adapters.sensors.vendor_stub import VendorStubAdapter


def test_simulation_moisture_in_documented_range():
    adapter = SimulationSensorAdapter()
    now = datetime.now(timezone.utc)
    r = adapter.read(uuid4(), "moisture", {}, now)
    assert 0.2 <= r.value <= 0.6
    assert r.unit == "vwc"
    assert r.source == "simulation"


def test_simulation_light_in_documented_range():
    adapter = SimulationSensorAdapter()
    now = datetime.now(timezone.utc)
    r = adapter.read(uuid4(), "light", {}, now)
    assert 200.0 <= r.value <= 2000.0
    assert r.source == "simulation"


def test_vendor_translate_maps_raw_fields_to_normalized_reading():
    device_id = uuid4()
    raw = {"value_pct": 45.0, "ts_ms": 1_700_000_000_000}
    r = VendorStubAdapter.translate(device_id, raw)
    assert r.value == 0.45
    assert r.unit == "vwc"
    assert r.source == "vendor"
    assert r.device_id == device_id


def test_vendor_read_generates_and_translates_without_network():
    adapter = VendorStubAdapter()
    now = datetime.now(timezone.utc)
    r = adapter.read(uuid4(), "moisture", {}, now)
    assert 0.0 <= r.value <= 1.0
    assert r.source == "vendor"


def test_mqtt_translate_maps_value_and_unit_no_socket():
    device_id = uuid4()
    now = datetime.now(timezone.utc)
    r = MqttSensorAdapter.translate(device_id, {"value": 0.41, "unit": "vwc"}, now)
    assert r.value == 0.41
    assert r.unit == "vwc"
    assert r.source == "mqtt"
    assert r.recorded_at == now