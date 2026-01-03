"""Add Google Drive fields to CourseAssignmentSubmission model

Revision ID: add_assignment_drive_fields
Revises: 20260103_120000
Create Date: 2026-01-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_assignment_drive_fields'
down_revision = '20260103_120000'
branch_labels = None
depends_on = None


def upgrade():
    # Add Google Drive fields to course_assignment_submission table
    op.add_column('course_assignment_submission', sa.Column('drive_file_id', sa.String(length=100), nullable=True))
    op.add_column('course_assignment_submission', sa.Column('drive_view_link', sa.String(length=300), nullable=True))


def downgrade():
    # Remove Google Drive fields from course_assignment_submission table
    op.drop_column('course_assignment_submission', 'drive_view_link')
    op.drop_column('course_assignment_submission', 'drive_file_id')