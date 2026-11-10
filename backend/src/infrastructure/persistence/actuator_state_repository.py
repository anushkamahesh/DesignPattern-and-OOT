from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import ActuatorStateRow, DeviceRow


class ActuatorStateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_actuators(self) -> list[tuple[DeviceRow, Optional[str]]]:
        """One query: every actuator with its stored state (None if it has no row yet)."""
        rows = self._session.execute(
            select(DeviceRow, ActuatorStateRow.state)
            .outerjoin(ActuatorStateRow, ActuatorStateRow.device_id == DeviceRow.id)
            .where(DeviceRow.role == "actuator")
            .order_by(DeviceRow.created_at, DeviceRow.id)
        ).all()
        return [(device, state) for device, state in rows]

    def get_actuator(self, device_id: UUID) -> Optional[tuple[DeviceRow, Optional[str]]]:
        row = self._session.execute(
            select(DeviceRow, ActuatorStateRow.state)
            .outerjoin(ActuatorStateRow, ActuatorStateRow.device_id == DeviceRow.id)
            .where(DeviceRow.id == device_id, DeviceRow.role == "actuator")
        ).first()
        return (row[0], row[1]) if row else None

    def get_state_info(self, device_id: UUID) -> Optional[tuple[str, datetime]]:
        """(state, updated_at) for the max-run-time policy; None when no row exists."""
        row = self._session.get(ActuatorStateRow, device_id)
        return (row.state, row.updated_at) if row else None

    def save_state(self, device_id: UUID, state: str) -> None:
        """Upsert the stored state in one transaction. updated_at is refreshed on
        every change, because it is the moment the actuator entered this state."""
        now = datetime.now(timezone.utc)
        try:
            row = self._session.get(ActuatorStateRow, device_id)
            if row is None:
                self._session.add(
                    ActuatorStateRow(device_id=device_id, state=state, updated_at=now)
                )
            else:
                row.state = state
                row.updated_at = now
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise