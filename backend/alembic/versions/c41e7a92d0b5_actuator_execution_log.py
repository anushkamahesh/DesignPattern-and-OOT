"""actuator_execution_log

Revision ID: c41e7a92d0b5
Revises: 7d2f9b3c41ae
Create Date: 2026-10-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c41e7a92d0b5'
down_revision: Union[str, Sequence[str], None] = '7d2f9b3c41ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('actuator_execution_log',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('device_id', sa.Uuid(), nullable=False),
    sa.Column('success', sa.Boolean(), nullable=False),
    sa.Column('policy_applied', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_actuator_execution_log_created_at', 'actuator_execution_log', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_actuator_execution_log_created_at', table_name='actuator_execution_log')
    op.drop_table('actuator_execution_log')