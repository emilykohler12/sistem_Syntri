"""email en users y tabla de códigos de recuperación de contraseña

Revision ID: 7a1e2c9f4b3d
Revises: cf327806fa65
Create Date: 2026-09-18 07:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7a1e2c9f4b3d'
down_revision: Union[str, Sequence[str], None] = 'cf327806fa65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))
    # Backfill: los usuarios que ya existían no tenían email. Usamos su
    # username (ya era único, así que no puede chocar con el índice único
    # que se crea después).
    op.execute("UPDATE users SET email = username WHERE email IS NULL")
    op.alter_column('users', 'email', nullable=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'password_reset_codes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('code_hash', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_password_reset_codes_user_id', 'password_reset_codes', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_password_reset_codes_user_id', table_name='password_reset_codes')
    op.drop_table('password_reset_codes')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_column('users', 'email')
