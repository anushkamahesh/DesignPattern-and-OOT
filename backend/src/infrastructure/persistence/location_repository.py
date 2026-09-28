from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from src.domain.locations.entity import Location, LocationConfig, Zone
from src.infrastructure.persistence.models import DeviceRow, LocationRow, ZoneRow


def _zone_from_row(row: ZoneRow) -> Zone:
    return Zone(
        id=row.id,
        name=row.name,
        moisture_threshold_low=float(row.moisture_threshold_low),
        moisture_threshold_high=float(row.moisture_threshold_high),
        schedule=dict(row.schedule or {}),
    )


class LocationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    # ---- reads ----
    def list_locations(self) -> Sequence[tuple[UUID, str]]:
        """Newest first."""
        stmt = select(LocationRow.id, LocationRow.name).order_by(
            LocationRow.created_at.desc()
        )
        return [(r.id, r.name) for r in self._session.execute(stmt).all()]

    def get_location(self, location_id: UUID) -> Optional[Location]:
        row = self._session.get(LocationRow, location_id)
        if row is None:
            return None
        zones = self._session.scalars(
            select(ZoneRow)
            .where(ZoneRow.location_id == location_id)
            .order_by(ZoneRow.name)
        ).all()
        return Location(
            id=row.id, name=row.name, zones=tuple(_zone_from_row(z) for z in zones)
        )

    def get_zone(self, location_id: UUID, zone_id: UUID) -> Optional[Zone]:
        row = self._session.scalars(
            select(ZoneRow).where(
                ZoneRow.id == zone_id, ZoneRow.location_id == location_id
            )
        ).first()
        return _zone_from_row(row) if row else None

    def count_zones(self, location_id: UUID) -> int:
        return self._session.scalar(
            select(func.count()).select_from(ZoneRow).where(ZoneRow.location_id == location_id)
        ) or 0

    # ---- writes (each is one transaction) ----
    def save_location_config(self, config: LocationConfig) -> Location:
        try:
            loc = LocationRow(name=config.location.name)
            self._session.add(loc)
            self._session.flush()
            self._session.add_all(
                ZoneRow(
                    location_id=loc.id,
                    name=z.name,
                    moisture_threshold_low=z.moisture_threshold_low,
                    moisture_threshold_high=z.moisture_threshold_high,
                    schedule=z.schedule,
                )
                for z in config.location.zones
            )
            self._session.commit()
            location_id = loc.id
        except Exception:
            self._session.rollback()
            raise
        return self.get_location(location_id)

    def delete_location(self, location_id: UUID) -> bool:
        # DB cascades: zones deleted; devices.zone_id and location_id set NULL.
        try:
            result = self._session.execute(
                delete(LocationRow).where(LocationRow.id == location_id)
            )
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        return result.rowcount > 0

    def add_zone(self, location_id: UUID, zone: Zone) -> Zone:
        try:
            row = ZoneRow(
                location_id=location_id,
                name=zone.name,
                moisture_threshold_low=zone.moisture_threshold_low,
                moisture_threshold_high=zone.moisture_threshold_high,
                schedule=zone.schedule,
            )
            self._session.add(row)
            self._session.commit()
            self._session.refresh(row)
        except Exception:
            self._session.rollback()
            raise
        return _zone_from_row(row)

    def update_zone(self, location_id: UUID, zone: Zone) -> Optional[Zone]:
        try:
            row = self._session.scalars(
                select(ZoneRow).where(
                    ZoneRow.id == zone.id, ZoneRow.location_id == location_id
                )
            ).first()
            if row is None:
                return None
            row.name = zone.name
            row.moisture_threshold_low = zone.moisture_threshold_low
            row.moisture_threshold_high = zone.moisture_threshold_high
            row.schedule = zone.schedule
            self._session.commit()
            self._session.refresh(row)
        except Exception:
            self._session.rollback()
            raise
        return _zone_from_row(row)

    def delete_zone(self, location_id: UUID, zone_id: UUID) -> bool:
        """Clears zone_id AND location_id on its devices, then deletes the zone."""
        try:
            self._session.execute(
                update(DeviceRow)
                .where(DeviceRow.zone_id == zone_id)
                .values(zone_id=None, location_id=None)
            )
            result = self._session.execute(
                delete(ZoneRow).where(
                    ZoneRow.id == zone_id, ZoneRow.location_id == location_id
                )
            )
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        return result.rowcount > 0