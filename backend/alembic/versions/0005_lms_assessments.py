"""LMS-02 assessments and quiz attempts

Revision ID: 0005_lms_assessments
Revises: d47869571d78
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_lms_assessments"
down_revision: Union[str, None] = "d47869571d78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lms_assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("pass_mark", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["lesson_id"], ["training_course_lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lesson_id", name="uq_lms_assessment_lesson"),
    )
    op.create_index("ix_lms_assessments_lesson_id", "lms_assessments", ["lesson_id"], unique=False)

    op.create_table(
        "lms_assessment_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("question_number", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("marks", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["lms_assessments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_id", "question_number", name="uq_lms_assessment_question_number"),
    )
    op.create_index("ix_lms_assessment_questions_assessment_id", "lms_assessment_questions", ["assessment_id"], unique=False)

    op.create_table(
        "lms_assessment_options",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("option_number", sa.Integer(), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["lms_assessment_questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id", "option_number", name="uq_lms_assessment_option_number"),
    )
    op.create_index("ix_lms_assessment_options_question_id", "lms_assessment_options", ["question_id"], unique=False)

    op.create_table(
        "lms_assessment_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("trainee_id", sa.Integer(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("max_score", sa.Integer(), nullable=False),
        sa.Column("percentage", sa.Integer(), nullable=False),
        sa.Column("result", sa.String(length=20), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["lms_assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trainee_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_id", "trainee_id", "attempt_number", name="uq_lms_attempt_number"),
    )
    op.create_index("ix_lms_assessment_attempts_assessment_id", "lms_assessment_attempts", ["assessment_id"], unique=False)
    op.create_index("ix_lms_assessment_attempts_trainee_id", "lms_assessment_attempts", ["trainee_id"], unique=False)

    op.create_table(
        "lms_assessment_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("selected_option_id", sa.Integer(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("awarded_marks", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["lms_assessment_attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["lms_assessment_questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["selected_option_id"], ["lms_assessment_options.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "question_id", name="uq_lms_attempt_question"),
    )
    op.create_index("ix_lms_assessment_answers_attempt_id", "lms_assessment_answers", ["attempt_id"], unique=False)
    op.create_index("ix_lms_assessment_answers_question_id", "lms_assessment_answers", ["question_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_lms_assessment_answers_question_id", table_name="lms_assessment_answers")
    op.drop_index("ix_lms_assessment_answers_attempt_id", table_name="lms_assessment_answers")
    op.drop_table("lms_assessment_answers")
    op.drop_index("ix_lms_assessment_attempts_trainee_id", table_name="lms_assessment_attempts")
    op.drop_index("ix_lms_assessment_attempts_assessment_id", table_name="lms_assessment_attempts")
    op.drop_table("lms_assessment_attempts")
    op.drop_index("ix_lms_assessment_options_question_id", table_name="lms_assessment_options")
    op.drop_table("lms_assessment_options")
    op.drop_index("ix_lms_assessment_questions_assessment_id", table_name="lms_assessment_questions")
    op.drop_table("lms_assessment_questions")
    op.drop_index("ix_lms_assessments_lesson_id", table_name="lms_assessments")
    op.drop_table("lms_assessments")
