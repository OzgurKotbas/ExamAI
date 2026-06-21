"""add free_quiz_count to user

Revision ID: 6bb13a99ab0c
Revises: 4c554c5d93b9
Create Date: 2026-06-13 03:01:55.945548

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6bb13a99ab0c'
down_revision = '4c554c5d93b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('free_quiz_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'free_quiz_count')
