"""add training ERP programme batch nomination enrollment tables

Revision ID: 0002_training_erp
Revises: 0001_common_foundation
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_training_erp"
down_revision = "0001_common_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "training_programmes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("mode", sa.String(40), nullable=False, server_default="HYBRID"),
        sa.Column("duration_days", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_training_programmes_institution_id", "training_programmes", ["institution_id"])
    op.create_index("ix_training_programmes_code", "training_programmes", ["code"], unique=True)

    op.create_table(
        "training_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("programme_id", sa.Integer(), nullable=False),
        sa.Column("batch_code", sa.String(60), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("trainer_id", sa.Integer(), nullable=True),
        sa.Column("venue", sa.String(200)),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("status", sa.String(30), nullable=False, server_default="PLANNED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["programme_id"], ["training_programmes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trainer_id"], ["users.id"]),
        sa.UniqueConstraint("programme_id", "batch_code", name="uq_batch_programme_code"),
    )
    op.create_index("ix_training_batches_programme_id", "training_batches", ["programme_id"])

    op.create_table(
        "training_nominations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("trainee_id", sa.Integer(), nullable=False),
        sa.Column("nominated_by_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="SUBMITTED"),
        sa.Column("remarks", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["training_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trainee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["nominated_by_id"], ["users.id"]),
        sa.UniqueConstraint("batch_id", "trainee_id", name="uq_nomination_batch_trainee"),
    )
    op.create_index("ix_training_nominations_batch_id", "training_nominations", ["batch_id"])
    op.create_index("ix_training_nominations_trainee_id", "training_nominations", ["trainee_id"])

    op.create_table(
        "training_enrollments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("trainee_id", sa.Integer(), nullable=False),
        sa.Column("nomination_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["training_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trainee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["nomination_id"], ["training_nominations.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("batch_id", "trainee_id", name="uq_enrollment_batch_trainee"),
        sa.UniqueConstraint("nomination_id"),
    )
    op.create_index("ix_training_enrollments_batch_id", "training_enrollments", ["batch_id"])
    op.create_index("ix_training_enrollments_trainee_id", "training_enrollments", ["trainee_id"])


def downgrade() -> None:
    op.drop_index("ix_training_enrollments_trainee_id", table_name="training_enrollments")
    op.drop_index("ix_training_enrollments_batch_id", table_name="training_enrollments")
    op.drop_table("training_enrollments")
    op.drop_index("ix_training_nominations_trainee_id", table_name="training_nominations")
    op.drop_index("ix_training_nominations_batch_id", table_name="training_nominations")
    op.drop_table("training_nominations")
    op.drop_index("ix_training_batches_programme_id", table_name="training_batches")
    op.drop_table("training_batches")
    op.drop_index("ix_training_programmes_code", table_name="training_programmes")
    op.drop_index("ix_training_programmes_institution_id", table_name="training_programmes")
    op.drop_table("training_programmes")
