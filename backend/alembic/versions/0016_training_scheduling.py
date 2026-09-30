"""ERP-08 training timetable and attendance linking"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0016_training_scheduling"
down_revision: Union[str, None] = "0015_career_employment_followups"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "training_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("training_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("training_courses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("module_id", sa.Integer(), sa.ForeignKey("training_course_modules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("trainer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("topic", sa.String(length=200), nullable=False),
        sa.Column("venue", sa.String(length=200), nullable=True),
        sa.Column("mode", sa.String(length=30), nullable=False, server_default="IN_PERSON"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="SCHEDULED"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("attendance_session_id", sa.Integer(), sa.ForeignKey("training_attendance_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("batch_id", "session_date", "start_time", name="uq_training_schedule_batch_date_start"),
        sa.UniqueConstraint("attendance_session_id", name="uq_training_schedule_attendance_session"),
    )
    op.create_index("ix_training_schedules_batch_id", "training_schedules", ["batch_id"])
    op.create_index("ix_training_schedules_course_id", "training_schedules", ["course_id"])
    op.create_index("ix_training_schedules_module_id", "training_schedules", ["module_id"])
    op.create_index("ix_training_schedules_trainer_id", "training_schedules", ["trainer_id"])
    op.create_index("ix_training_schedules_session_date", "training_schedules", ["session_date"])
    op.create_index("ix_training_schedules_status", "training_schedules", ["status"])


def downgrade() -> None:
    op.drop_index("ix_training_schedules_status", table_name="training_schedules")
    op.drop_index("ix_training_schedules_session_date", table_name="training_schedules")
    op.drop_index("ix_training_schedules_trainer_id", table_name="training_schedules")
    op.drop_index("ix_training_schedules_module_id", table_name="training_schedules")
    op.drop_index("ix_training_schedules_course_id", table_name="training_schedules")
    op.drop_index("ix_training_schedules_batch_id", table_name="training_schedules")
    op.drop_table("training_schedules")
