"""Credential revocation management

Revision ID: 0010_credential_revocation
Revises: 0009_attendance_operations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0010_credential_revocation"
down_revision: Union[str, None] = "0009_attendance_operations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("training_credentials", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("training_credentials", sa.Column("revoked_by_id", sa.Integer(), nullable=True))
    op.add_column("training_credentials", sa.Column("revocation_reason", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_training_credentials_revoked_by",
        "training_credentials",
        "users",
        ["revoked_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_training_credentials_revoked_by_id", "training_credentials", ["revoked_by_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_training_credentials_revoked_by_id", table_name="training_credentials")
    op.drop_constraint("fk_training_credentials_revoked_by", "training_credentials", type_="foreignkey")
    op.drop_column("training_credentials", "revocation_reason")
    op.drop_column("training_credentials", "revoked_by_id")
    op.drop_column("training_credentials", "revoked_at")
