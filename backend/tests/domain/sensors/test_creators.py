from src.domain.sensors.creators import (
    LightSensorCreator,
    MoistureSensorCreator,
)


def test_moisture_creator_creates_moisture_sensor():
    sensor = MoistureSensorCreator().create_sensor()

    assert sensor.device_type == "moisture"
    assert sensor.default_config["unit"] == "%"


def test_light_creator_creates_light_sensor():
    sensor = LightSensorCreator().create_sensor()

    assert sensor.device_type == "light"
    assert sensor.default_config["unit"] == "lux"


def test_creators_have_different_defaults():
    moisture = MoistureSensorCreator().create_sensor()
    light = LightSensorCreator().create_sensor()

    assert moisture.default_config != light.default_config
