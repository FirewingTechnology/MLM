"""add_matching_commission_to_settlements

Revision ID: 9a8b7c6d5e4f
Revises: 67003a6bff01
Create Date: 2026-08-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a8b7c6d5e4f'
down_revision: Union[str, None] = '67003a6bff01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('slot_settlements', schema=None) as batch_op:
        batch_op.add_column(sa.Column('matching_commission', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    with op.batch_alter_table('slot_settlements', schema=None) as batch_op:
        batch_op.drop_column('matching_commission')
