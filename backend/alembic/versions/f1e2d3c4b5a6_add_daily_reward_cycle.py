"""add_daily_reward_cycle

Revision ID: f1e2d3c4b5a6
Revises: e8f9a0b1c2d3
Create Date: 2026-09-19 07:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f1e2d3c4b5a6'
down_revision: Union[str, None] = 'e8f9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tables are managed additively via Base.metadata and apply_migrations
    pass


def downgrade() -> None:
    pass
