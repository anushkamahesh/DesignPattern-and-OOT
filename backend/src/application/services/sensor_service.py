from sqlalchemy.orm import Session
from ...domain.sensors.creators import get_sensor_creator
from ...domain.sensors.entity import Sensor
from ...infrastructure.persistence.repository import SensorRepository


class SensorService:
    def __init__(self, session: Session):
        self.repository = SensorRepository(session)

    def create_sensor(self, sensor_type: str, display_name: str | None = None) -> Sensor:
        creator = get_sensor_creator(sensor_type)
        if not creator:
            raise ValueError(f"Unknown sensor type: '{sensor_type}'")

        sensor = creator.create_sensor(display_name=display_name)
        return self.repository.save(sensor)

    def list_sensors(self) -> list[Sensor]:
        return self.repository.get_all_sensors()
