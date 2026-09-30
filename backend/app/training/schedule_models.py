from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TrainingSchedule(Base):
    __tablename__ = "training_schedules"
    __table_args__ = (
        UniqueConstraint("batch_id", "session_date", "start_time", name="uq_training_schedule_batch_date_start"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("training_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("training_courses.id", ondelete="SET NULL"), nullable=True, index=True)
    module_id: Mapped[int | None] = mapped_column(ForeignKey("training_course_modules.id", ondelete="SET NULL"), nullable=True, index=True)
    trainer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    venue: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mode: Mapped[str] = mapped_column(String(30), nullable=False, default="IN_PERSON")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="SCHEDULED", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    attendance_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("training_attendance_sessions.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
