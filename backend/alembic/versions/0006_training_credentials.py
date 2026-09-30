"""LMS-03 training credentials

Revision ID: 0006_training_credentials
Revises: 0005_lms_assessments
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_training_credentials"
down_revision: Union[str, None] = "0005_lms_assessments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "training_credentials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trainee_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("credential_number", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("course_title", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("score_percentage", sa.Integer(), nullable=False),
        sa.Column("completed_lessons", sa.Integer(), nullable=False),
        sa.Column("total_lessons", sa.Integer(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["trainee_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["training_courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trainee_id", "course_id", name="uq_training_credential_trainee_course"),
        sa.UniqueConstraint("credential_number", name="uq_training_credential_number"),
    )
    op.create_index("ix_training_credentials_trainee_id", "training_credentials", ["trainee_id"], unique=False)
    op.create_index("ix_training_credentials_course_id", "training_credentials", ["course_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_training_credentials_course_id", table_name="training_credentials")
    op.drop_index("ix_training_credentials_trainee_id", table_name="training_credentials")
    op.drop_table("training_credentials")
