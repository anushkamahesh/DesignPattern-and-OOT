"""actuator_states

Revision ID: 7d2f9b3c41ae
Revises: 5217c3a1ab62
Create Date: 2026-10-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d2f9b3c41ae'
down_revision: Union[str, Sequence[str], None] = '5217c3a1ab62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('actuator_states',
    sa.Column('device_id', sa.Uuid(), nullable=False),
    sa.Column('state', sa.String(length=32), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('device_id')
    )

    # Seed: every existing actuator starts idle. Actuators created later get
    # their row on their first transition; until then a missing row reads as idle.
    op.execute(
        sa.text(
            "INSERT INTO actuator_states (device_id, state) "
            "SELECT id, 'idle' FROM devices WHERE role = 'actuator'"
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('actuator_states')