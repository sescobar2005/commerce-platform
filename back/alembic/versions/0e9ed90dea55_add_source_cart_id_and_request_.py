"""add source_cart_id and request_fingerprint to orders

Revision ID: 0e9ed90dea55
Revises: 8e7f6d5c4b3a
Create Date: 2026-11-26 19:02:24.087529+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e9ed90dea55'
down_revision: Union[str, Sequence[str], None] = '8e7f6d5c4b3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('orders', sa.Column('source_cart_id', sa.String(length=36), nullable=True, comment='Source cart identifier for idempotency retry scenarios'))
    op.add_column('orders', sa.Column('request_fingerprint', sa.String(length=64), nullable=True, comment='SHA-256 fingerprint of canonical cart representation for idempotency'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('orders', 'request_fingerprint')
    op.drop_column('orders', 'source_cart_id')
