from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from .models import DeviceRow
from ...domain.sensors.entity import Sensor


class SensorRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, sensor: Sensor) -> Sensor:
        device_row = DeviceRow(
            device_type=sensor.device_type,
            role="sensor",
            display_name=sensor.display_name,
            default_config=sensor.default_config,
        )
        self.session.add(device_row)
        self.session.commit()
        self.session.refresh(device_row)

        return Sensor(
            id=device_row.id,
            device_type=device_row.device_type,
            display_name=device_row.display_name,
            default_config=device_row.default_config,
        )

    def get_all_sensors(self) -> list[Sensor]:
        stmt = select(DeviceRow).where(DeviceRow.role == "sensor")
        results = self.session.scalars(stmt).all()

        return [
            Sensor(
                id=row.id,
                device_type=row.device_type,
                display_name=row.display_name,
                default_config=row.default_config,
            )
            for row in results
        ]
