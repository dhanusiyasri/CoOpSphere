from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class TrainingSessionFeedback(Base):
    __tablename__ = "training_session_feedback"
    __table_args__ = (UniqueConstraint("schedule_id", "trainee_id", name="uq_training_feedback_schedule_trainee"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("training_schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("training_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    trainee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    trainer_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    venue_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
