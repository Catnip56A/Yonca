"""Add user-resource access tracking for permanent resource access after PIN verification

Revision ID: 20260103_120000
Revises: add_drive_fields
Create Date: 2026-01-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260103_120000'
down_revision = 'add_drive_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_resource_access association table
    op.create_table('user_resource_access',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('accessed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['resource_id'], ['resource.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'resource_id')
    )


def downgrade():
    # Drop user_resource_access association table
    op.drop_table('user_resource_access')