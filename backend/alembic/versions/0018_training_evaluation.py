"""ERP-10 training session evaluation and feedback"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision: str = "0018_training_evaluation"
down_revision: Union[str, None] = "0017_training_logistics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "training_session_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("training_schedules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("training_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trainee_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_rating", sa.Integer(), nullable=False),
        sa.Column("trainer_rating", sa.Integer(), nullable=False),
        sa.Column("venue_rating", sa.Integer(), nullable=False),
        sa.Column("overall_rating", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("schedule_id", "trainee_id", name="uq_training_feedback_schedule_trainee"),
    )
    op.create_index("ix_training_session_feedback_schedule_id", "training_session_feedback", ["schedule_id"])
    op.create_index("ix_training_session_feedback_batch_id", "training_session_feedback", ["batch_id"])
    op.create_index("ix_training_session_feedback_trainee_id", "training_session_feedback", ["trainee_id"])

def downgrade() -> None:
    op.drop_index("ix_training_session_feedback_trainee_id", table_name="training_session_feedback")
    op.drop_index("ix_training_session_feedback_batch_id", table_name="training_session_feedback")
    op.drop_index("ix_training_session_feedback_schedule_id", table_name="training_session_feedback")
    op.drop_table("training_session_feedback")
