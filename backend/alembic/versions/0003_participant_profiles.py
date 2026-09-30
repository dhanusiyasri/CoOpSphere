"""add training participant profiles

Revision ID: 0003_participant_profiles
Revises: 0002_training_erp
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_participant_profiles"
down_revision = "0002_training_erp"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "training_participant_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("participant_code", sa.String(40), nullable=False),
        sa.Column("phone", sa.String(30)),
        sa.Column("participant_type", sa.String(50), nullable=False, server_default="RURAL_YOUTH"),
        sa.Column("designation", sa.String(120)),
        sa.Column("organization_name", sa.String(200)),
        sa.Column("education_level", sa.String(100)),
        sa.Column("district", sa.String(100)),
        sa.Column("state", sa.String(100)),
        sa.Column("digital_literacy_level", sa.String(30), nullable=False, server_default="BASIC"),
        sa.Column("years_experience", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("profile_status", sa.String(30), nullable=False, server_default="INCOMPLETE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("participant_code"),
    )
    op.create_index("ix_training_participant_profiles_user_id", "training_participant_profiles", ["user_id"])
    op.create_index("ix_training_participant_profiles_participant_code", "training_participant_profiles", ["participant_code"], unique=True)

def downgrade() -> None:
    op.drop_index("ix_training_participant_profiles_participant_code", table_name="training_participant_profiles")
    op.drop_index("ix_training_participant_profiles_user_id", table_name="training_participant_profiles")
    op.drop_table("training_participant_profiles")
