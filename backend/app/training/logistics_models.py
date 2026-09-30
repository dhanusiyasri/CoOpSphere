from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class TrainingLogisticsPlan(Base):
    __tablename__ = "training_logistics_plans"
    __table_args__ = (UniqueConstraint("batch_id", name="uq_training_logistics_batch"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("training_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    hostel_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hostel_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rooms_available: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meals_included: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    meal_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    transport_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pickup_point: Mapped[str | None] = mapped_column(String(300), nullable=True)
    transport_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    coordinator_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    coordinator_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class TrainingAccommodationAllocation(Base):
    __tablename__ = "training_accommodation_allocations"
    __table_args__ = (UniqueConstraint("batch_id", "trainee_id", name="uq_training_accommodation_batch_trainee"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("training_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    trainee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    room_number: Mapped[str] = mapped_column(String(50), nullable=False)
    bed_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ALLOCATED")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    allocated_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    allocated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
