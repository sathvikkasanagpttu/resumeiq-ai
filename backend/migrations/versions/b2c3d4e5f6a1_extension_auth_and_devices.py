"""extension auth and devices tables

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-10-07 11:51:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a1'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'extension_devices',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('device_id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('device_name', sa.String(100), nullable=True),
        sa.Column('hashed_refresh_token', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_extension_devices_device_id', 'extension_devices', ['device_id'])
    op.create_index('ix_extension_devices_user_id', 'extension_devices', ['user_id'])
    op.create_index('ix_extension_devices_revoked_at', 'extension_devices', ['revoked_at'])

    op.create_table(
        'extension_pairing_codes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code_hash', sa.String(64), nullable=False),
        sa.Column('is_used', sa.Boolean(), default=False, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_extension_pairing_codes_user_id', 'extension_pairing_codes', ['user_id'])
    op.create_index('ix_extension_pairing_codes_code_hash', 'extension_pairing_codes', ['code_hash'])
    op.create_index('ix_extension_pairing_codes_expires_at', 'extension_pairing_codes', ['expires_at'])


def downgrade() -> None:
    op.drop_table('extension_pairing_codes')
    op.drop_table('extension_devices')
