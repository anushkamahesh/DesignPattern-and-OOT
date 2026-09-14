from abc import ABC, abstractmethod
from .entity import Sensor


class SensorCreator(ABC):
    @abstractmethod
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        pass


class MoistureSensorCreator(SensorCreator):
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        return Sensor(
            id=None,
            device_type="moisture",
            display_name=display_name or "Moisture Sensor",
            default_config={
                "unit": "%",
                "min": 0,
                "max": 100,
            },
        )


class LightSensorCreator(SensorCreator):
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        return Sensor(
            id=None,
            device_type="light",
            display_name=display_name or "Light Sensor",
            default_config={
                "unit": "lux",
                "min": 0,
                "max": 100000,
            },
        )


CREATORS: dict[str, SensorCreator] = {
    "moisture": MoistureSensorCreator(),
    "light": LightSensorCreator(),
}


def get_sensor_creator(sensor_type: str) -> SensorCreator | None:
    return CREATORS.get(sensor_type)
