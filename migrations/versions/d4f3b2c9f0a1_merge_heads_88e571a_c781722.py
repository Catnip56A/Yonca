"""Merge heads

Revision ID: d4f3b2c9f0a1
Revises: 88e571a01ac0
Create Date: 2026-01-28 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4f3b2c9f0a1'
down_revision = '88e571a01ac0'
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration; no schema changes required.
    pass


def downgrade():
    # No downgrade steps for the merge revision.
    pass


