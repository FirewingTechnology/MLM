"""postgresql_production_schema

Revision ID: e8f9a0b1c2d3
Revises: 9a8b7c6d5e4f
Create Date: 2026-08-31 19:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e8f9a0b1c2d3'
down_revision: Union[str, None] = '9a8b7c6d5e4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # All tables and constraints are defined in Base.metadata and managed additively
    pass


def downgrade() -> None:
    pass
