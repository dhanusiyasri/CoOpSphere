"""Careers employment exchange

Revision ID: 0007_careers_employment
Revises: 0006_training_credentials
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0007_careers_employment"
down_revision: Union[str, None] = "0006_training_credentials"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "career_job_postings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("organization_name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=160), nullable=False),
        sa.Column("employment_type", sa.String(length=40), nullable=False),
        sa.Column("skills", sa.String(length=500), nullable=True),
        sa.Column("minimum_education", sa.String(length=120), nullable=True),
        sa.Column("minimum_experience_years", sa.Integer(), nullable=False),
        sa.Column("salary_range", sa.String(length=120), nullable=True),
        sa.Column("closing_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_job_postings_employer_id", "career_job_postings", ["employer_id"], unique=False)

    op.create_table(
        "career_job_applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("trainee_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("cover_note", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["career_job_postings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trainee_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "trainee_id", name="uq_career_job_application_job_trainee"),
    )
    op.create_index("ix_career_job_applications_job_id", "career_job_applications", ["job_id"], unique=False)
    op.create_index("ix_career_job_applications_trainee_id", "career_job_applications", ["trainee_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_career_job_applications_trainee_id", table_name="career_job_applications")
    op.drop_index("ix_career_job_applications_job_id", table_name="career_job_applications")
    op.drop_table("career_job_applications")
    op.drop_index("ix_career_job_postings_employer_id", table_name="career_job_postings")
    op.drop_table("career_job_postings")
