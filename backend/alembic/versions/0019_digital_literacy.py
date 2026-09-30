"""skills-01 digital literacy assessment

Revision ID: 0019_digital_literacy
Revises: 0018_training_evaluation
"""
from alembic import op
import sqlalchemy as sa

revision = "0019_digital_literacy"
down_revision = "0018_training_evaluation"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "digital_literacy_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trainee_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("percentage", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(length=30), nullable=False),
        sa.Column("answers_json", sa.Text(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_digital_literacy_attempts_trainee_id", "digital_literacy_attempts", ["trainee_id"])

def downgrade():
    op.drop_index("ix_digital_literacy_attempts_trainee_id", table_name="digital_literacy_attempts")
    op.drop_table("digital_literacy_attempts")
