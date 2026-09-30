from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Credential(Base):
    __tablename__ = "training_credentials"
    __table_args__ = (
        UniqueConstraint("trainee_id", "course_id", name="uq_training_credential_trainee_course"),
        UniqueConstraint("credential_number", name="uq_training_credential_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trainee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("training_courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    credential_number: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    course_title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ISSUED")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    issued_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_lessons: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_lessons: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
