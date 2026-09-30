"""Credential issuance audit actor

Revision ID: 0011_credential_issuance_audit
Revises: 0010_credential_revocation
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0011_credential_issuance_audit"
down_revision: Union[str, None] = "0010_credential_revocation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("training_credentials", sa.Column("issued_by_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_training_credentials_issued_by",
        "training_credentials",
        "users",
        ["issued_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_training_credentials_issued_by_id", "training_credentials", ["issued_by_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_training_credentials_issued_by_id", table_name="training_credentials")
    op.drop_constraint("fk_training_credentials_issued_by", "training_credentials", type_="foreignkey")
    op.drop_column("training_credentials", "issued_by_id")
