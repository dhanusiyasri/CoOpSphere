"""LMS-01 lesson progress

Revision ID: d47869571d78
Revises: 0004_training_courses
Create Date: 2026-09-29 16:52:41.172017
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d47869571d78"
down_revision: Union[str, None] = "0004_training_courses"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "training_lesson_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trainee_id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["lesson_id"], ["training_course_lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trainee_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trainee_id", "lesson_id", name="uq_lesson_progress_trainee_lesson"),
    )
    op.create_index("ix_training_lesson_progress_trainee_id", "training_lesson_progress", ["trainee_id"], unique=False)
    op.create_index("ix_training_lesson_progress_lesson_id", "training_lesson_progress", ["lesson_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_training_lesson_progress_lesson_id", table_name="training_lesson_progress")
    op.drop_index("ix_training_lesson_progress_trainee_id", table_name="training_lesson_progress")
    op.drop_table("training_lesson_progress")
