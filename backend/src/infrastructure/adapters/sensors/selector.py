from __future__ import annotations

from src.domain.sensors.ports import SensorPort
from src.infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from src.infrastructure.adapters.sensors.vendor_stub import VendorStubAdapter

# Selection rule (documented here and in docs/patterns/adapter.md):
#   default_config.protocol == "mqtt"       -> no one-shot adapter; MQTT
#                                               readings arrive only via
#                                               MqttSensorAdapter.translate()
#                                               from an inbound payload.
#   default_config.protocol == "simulation" -> SimulationSensorAdapter,
#                                               UNLESS default_config.vendor
#                                               == "stub", in which case the
#                                               vendor stub is used instead.
#                                               This keeps "which family"
#                                               (protocol) separate from
#                                               "which concrete driver"
#                                               (vendor flag).


def select_sensor_adapter(default_config: dict) -> SensorPort:
    config = default_config or {}
    protocol = config.get("protocol", "simulation")

    if protocol == "mqtt":
        raise ValueError(
            "mqtt devices do not support a manual read; readings arrive via ingest"
        )

    if config.get("vendor") == "stub":
        return VendorStubAdapter()

    return SimulationSensorAdapter()