from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import ActuatorExecutionLogRow


class ExecutionLogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def insert(
        self,
        device_id: UUID,
        success: bool,
        policy_applied: list[str],
        message: Optional[str],
    ) -> ActuatorExecutionLogRow:
        row = ActuatorExecutionLogRow(
            device_id=device_id,
            success=success,
            policy_applied=list(policy_applied),
            message=message,
        )
        try:
            self._session.add(row)
            self._session.commit()
            self._session.refresh(row)
        except Exception:
            self._session.rollback()
            raise
        return row

    def list_recent(self, limit: int = 20) -> Sequence[ActuatorExecutionLogRow]:
        return self._session.scalars(
            select(ActuatorExecutionLogRow)
            .order_by(ActuatorExecutionLogRow.created_at.desc())
            .limit(limit)
        ).all()