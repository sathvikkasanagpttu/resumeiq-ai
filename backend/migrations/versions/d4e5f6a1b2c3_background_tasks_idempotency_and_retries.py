"""background tasks idempotency and retries upgrade

Revision ID: d4e5f6a1b2c3
Revises: c3d4e5f6a1b2
Create Date: 2026-10-07 13:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a1b2c3'
down_revision: Union[str, None] = 'c3d4e5f6a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    with op.batch_alter_table('background_tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('idempotency_key', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('max_retries', sa.Integer(), server_default='3', nullable=False))
        batch_op.create_index('ix_background_tasks_idempotency_key', ['idempotency_key'], unique=True)

def downgrade() -> None:
    with op.batch_alter_table('background_tasks', schema=None) as batch_op:
        batch_op.drop_index('ix_background_tasks_idempotency_key')
        batch_op.drop_column('max_retries')
        batch_op.drop_column('retry_count')
        batch_op.drop_column('idempotency_key')
