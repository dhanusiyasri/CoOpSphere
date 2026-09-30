"""Careers-08 employment follow-up tracking"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0015_career_employment_followups"
down_revision: Union[str, None] = "0014_career_placement_outcomes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "career_employment_followups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("placement_id", sa.Integer(), sa.ForeignKey("career_employment_outcomes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trainee_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("checkpoint", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="CONTINUING"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("employer_feedback", sa.Text(), nullable=True),
        sa.Column("trainee_feedback", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("placement_id", "checkpoint", name="uq_career_followup_placement_checkpoint"),
    )
    op.create_index("ix_career_employment_followups_placement_id", "career_employment_followups", ["placement_id"])
    op.create_index("ix_career_employment_followups_trainee_id", "career_employment_followups", ["trainee_id"])
    op.create_index("ix_career_employment_followups_employer_id", "career_employment_followups", ["employer_id"])

def downgrade() -> None:
    op.drop_index("ix_career_employment_followups_employer_id", table_name="career_employment_followups")
    op.drop_index("ix_career_employment_followups_trainee_id", table_name="career_employment_followups")
    op.drop_index("ix_career_employment_followups_placement_id", table_name="career_employment_followups")
    op.drop_table("career_employment_followups")
