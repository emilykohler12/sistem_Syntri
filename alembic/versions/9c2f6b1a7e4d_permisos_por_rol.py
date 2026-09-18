"""agregar permissions a roles

Revision ID: 9c2f6b1a7e4d
Revises: 7a1e2c9f4b3d
Create Date: 2026-09-18 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9c2f6b1a7e4d'
down_revision: Union[str, Sequence[str], None] = '7a1e2c9f4b3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('roles', sa.Column('permissions', sa.String(), nullable=True))
    op.execute("UPDATE roles SET permissions = '' WHERE name != 'admin'")
    op.execute("UPDATE roles SET permissions = 'messages,metrics,users,roles,limits' WHERE name = 'admin'")
    op.alter_column('roles', 'permissions', nullable=False, server_default='')


def downgrade() -> None:
    op.drop_column('roles', 'permissions')
