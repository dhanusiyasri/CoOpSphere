"""ERP-09 training logistics and accommodation"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0017_training_logistics"
down_revision: Union[str, None] = "0016_training_scheduling"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "training_logistics_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("training_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hostel_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("hostel_name", sa.String(200), nullable=True),
        sa.Column("rooms_available", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meals_included", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("meal_notes", sa.String(500), nullable=True),
        sa.Column("transport_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("pickup_point", sa.String(300), nullable=True),
        sa.Column("transport_notes", sa.String(500), nullable=True),
        sa.Column("coordinator_name", sa.String(150), nullable=True),
        sa.Column("coordinator_phone", sa.String(40), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("batch_id", name="uq_training_logistics_batch"),
    )
    op.create_index("ix_training_logistics_plans_batch_id","training_logistics_plans",["batch_id"])
    op.create_table(
        "training_accommodation_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("training_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trainee_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("room_number", sa.String(50), nullable=False),
        sa.Column("bed_number", sa.String(50), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="ALLOCATED"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("allocated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("allocated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("batch_id","trainee_id",name="uq_training_accommodation_batch_trainee"),
    )
    op.create_index("ix_training_accommodation_allocations_batch_id","training_accommodation_allocations",["batch_id"])
    op.create_index("ix_training_accommodation_allocations_trainee_id","training_accommodation_allocations",["trainee_id"])

def downgrade() -> None:
    op.drop_index("ix_training_accommodation_allocations_trainee_id", table_name="training_accommodation_allocations")
    op.drop_index("ix_training_accommodation_allocations_batch_id", table_name="training_accommodation_allocations")
    op.drop_table("training_accommodation_allocations")
    op.drop_index("ix_training_logistics_plans_batch_id", table_name="training_logistics_plans")
    op.drop_table("training_logistics_plans")
