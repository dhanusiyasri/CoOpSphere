"""attendance operations

Revision ID: 0009_attendance_operations
Revises: 0008_career_profiles_matching
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0009_attendance_operations"
down_revision: Union[str, None] = "0008_career_profiles_matching"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "training_attendance_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("training_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("topic", sa.String(length=200), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="SCHEDULED"),
        sa.Column("access_code", sa.String(length=20), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("batch_id", "session_date", "start_time", name="uq_attendance_session_batch_date_start"),
        sa.UniqueConstraint("access_code", name="uq_training_attendance_sessions_access_code"),
    )
    op.create_index("ix_training_attendance_sessions_batch_id", "training_attendance_sessions", ["batch_id"])
    op.create_index("ix_training_attendance_sessions_session_date", "training_attendance_sessions", ["session_date"])
    op.create_index("ix_training_attendance_sessions_status", "training_attendance_sessions", ["status"])
    op.create_index("ix_training_attendance_sessions_access_code", "training_attendance_sessions", ["access_code"])

    op.create_table(
        "training_attendance_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("training_attendance_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trainee_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PRESENT"),
        sa.Column("method", sa.String(length=20), nullable=False, server_default="MANUAL"),
        sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("marked_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("remarks", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("session_id", "trainee_id", name="uq_attendance_session_trainee"),
    )
    op.create_index("ix_training_attendance_records_session_id", "training_attendance_records", ["session_id"])
    op.create_index("ix_training_attendance_records_trainee_id", "training_attendance_records", ["trainee_id"])


def downgrade() -> None:
    op.drop_index("ix_training_attendance_records_trainee_id", table_name="training_attendance_records")
    op.drop_index("ix_training_attendance_records_session_id", table_name="training_attendance_records")
    op.drop_table("training_attendance_records")
    op.drop_index("ix_training_attendance_sessions_access_code", table_name="training_attendance_sessions")
    op.drop_index("ix_training_attendance_sessions_status", table_name="training_attendance_sessions")
    op.drop_index("ix_training_attendance_sessions_session_date", table_name="training_attendance_sessions")
    op.drop_index("ix_training_attendance_sessions_batch_id", table_name="training_attendance_sessions")
    op.drop_table("training_attendance_sessions")
