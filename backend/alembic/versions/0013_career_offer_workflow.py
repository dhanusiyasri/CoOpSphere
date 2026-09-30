"""Careers-05 offer workflow"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0013_career_offer_workflow"
down_revision: Union[str, None] = "0012_career_interview_scheduling"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("career_job_applications", sa.Column("offer_status", sa.String(length=30), nullable=True))
    op.add_column("career_job_applications", sa.Column("offer_offered_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("career_job_applications", sa.Column("offer_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("career_job_applications", sa.Column("offer_salary", sa.String(length=120), nullable=True))
    op.add_column("career_job_applications", sa.Column("offer_employment_type", sa.String(length=40), nullable=True))
    op.add_column("career_job_applications", sa.Column("offer_notes", sa.Text(), nullable=True))
    op.add_column("career_job_applications", sa.Column("offer_responded_at", sa.DateTime(timezone=True), nullable=True))

def downgrade() -> None:
    for name in ["offer_responded_at","offer_notes","offer_employment_type","offer_salary","offer_expires_at","offer_offered_at","offer_status"]:
        op.drop_column("career_job_applications", name)
