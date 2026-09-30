"""Careers-04 interview scheduling"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0012_career_interview_scheduling"
down_revision: Union[str, None] = "0011_credential_issuance_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("career_job_applications", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("career_job_applications", sa.Column("interview_scheduled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("career_job_applications", sa.Column("interview_mode", sa.String(length=30), nullable=True))
    op.add_column("career_job_applications", sa.Column("interview_location_or_link", sa.String(length=500), nullable=True))
    op.add_column("career_job_applications", sa.Column("interview_notes", sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column("career_job_applications", "interview_notes")
    op.drop_column("career_job_applications", "interview_location_or_link")
    op.drop_column("career_job_applications", "interview_mode")
    op.drop_column("career_job_applications", "interview_scheduled_at")
    op.drop_column("career_job_applications", "updated_at")
