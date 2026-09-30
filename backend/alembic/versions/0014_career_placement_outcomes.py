"""Careers-06 placement outcomes"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0014_career_placement_outcomes"
down_revision: Union[str, None] = "0013_career_offer_workflow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "career_employment_outcomes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("career_job_applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trainee_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING_JOINING"),
        sa.Column("joining_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("application_id", name="uq_career_employment_outcome_application"),
    )
    op.execute("""
        INSERT INTO career_employment_outcomes (application_id, trainee_id, employer_id, status)
        SELECT a.id, a.trainee_id, j.employer_id, 'PENDING_JOINING'
        FROM career_job_applications a
        JOIN career_job_postings j ON j.id = a.job_id
        WHERE a.offer_status = 'ACCEPTED'
          AND NOT EXISTS (SELECT 1 FROM career_employment_outcomes e WHERE e.application_id = a.id)
    """)
    op.create_index("ix_career_employment_outcomes_application_id", "career_employment_outcomes", ["application_id"])
    op.create_index("ix_career_employment_outcomes_trainee_id", "career_employment_outcomes", ["trainee_id"])
    op.create_index("ix_career_employment_outcomes_employer_id", "career_employment_outcomes", ["employer_id"])

def downgrade() -> None:
    op.drop_index("ix_career_employment_outcomes_employer_id", table_name="career_employment_outcomes")
    op.drop_index("ix_career_employment_outcomes_trainee_id", table_name="career_employment_outcomes")
    op.drop_index("ix_career_employment_outcomes_application_id", table_name="career_employment_outcomes")
    op.drop_table("career_employment_outcomes")
