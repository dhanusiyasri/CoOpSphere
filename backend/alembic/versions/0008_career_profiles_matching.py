"""Career profile and matching

Revision ID: 0008_career_profiles_matching
Revises: 0007_careers_employment
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0008_career_profiles_matching"
down_revision: Union[str, None] = "0007_careers_employment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "career_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trainee_id", sa.Integer(), nullable=False),
        sa.Column("headline", sa.String(length=160), nullable=True),
        sa.Column("professional_summary", sa.Text(), nullable=True),
        sa.Column("skills", sa.String(length=1000), nullable=True),
        sa.Column("preferred_locations", sa.String(length=500), nullable=True),
        sa.Column("preferred_employment_types", sa.String(length=300), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=True),
        sa.Column("profile_visibility", sa.String(length=20), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["trainee_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trainee_id"),
    )
    op.create_index("ix_career_profiles_trainee_id", "career_profiles", ["trainee_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_career_profiles_trainee_id", table_name="career_profiles")
    op.drop_table("career_profiles")
