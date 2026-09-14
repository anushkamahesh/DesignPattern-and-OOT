from sqlalchemy import select
from sqlalchemy.orm import Session
from ...domain.sensors.entity import Sensor
from .models import DeviceRow


class DeviceRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_sensor(self, sensor: Sensor) -> Sensor:
        row = DeviceRow(
            device_type=sensor.device_type,
            role="sensor",
            display_name=sensor.display_name,
            default_config=sensor.default_config,
        )

        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)

        return Sensor(
            id=row.id,
            device_type=row.device_type,
            display_name=row.display_name or "",
            default_config=row.default_config,
        )

    def list_sensors(self) -> list[Sensor]:
        statement = (
            select(DeviceRow)
            .where(DeviceRow.role == "sensor")
            .order_by(DeviceRow.created_at.desc())
        )

        rows = self.session.scalars(statement).all()

        return [
            Sensor(
                id=row.id,
                device_type=row.device_type,
                display_name=row.display_name or "",
                default_config=row.default_config,
            )
            for row in rows
        ]
