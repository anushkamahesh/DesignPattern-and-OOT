from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import AutomationRuleRow, DeviceRow, ReadingRow


class AutomationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_rule(self, location_id: UUID) -> Optional[AutomationRuleRow]:
        return self._session.scalars(
            select(AutomationRuleRow).where(AutomationRuleRow.location_id == location_id)
        ).first()

    def upsert_rule(self, location_id: UUID, strategy_key: str) -> AutomationRuleRow:
        try:
            row = self.get_rule(location_id)
            if row is None:
                row = AutomationRuleRow(location_id=location_id, strategy_key=strategy_key)
                self._session.add(row)
            else:
                row.strategy_key = strategy_key
                row.updated_at = datetime.now(timezone.utc)
            self._session.commit()
            self._session.refresh(row)
            return row
        except Exception:
            self._session.rollback()
            raise

    def latest_zone_value(self, zone_id: UUID, device_type: str) -> Optional[float]:
        """Latest stored reading among sensors of that type assigned to the zone.
        Unassigned devices are never considered."""
        value = self._session.scalars(
            select(ReadingRow.value)
            .join(DeviceRow, DeviceRow.id == ReadingRow.device_id)
            .where(DeviceRow.zone_id == zone_id, DeviceRow.device_type == device_type)
            .order_by(ReadingRow.recorded_at.desc())
            .limit(1)
        ).first()
        return float(value) if value is not None else None