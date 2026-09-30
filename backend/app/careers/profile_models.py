from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CareerProfile(Base):
    __tablename__ = "career_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trainee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    headline: Mapped[str | None] = mapped_column(String(160), nullable=True)
    professional_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    preferred_locations: Mapped[str | None] = mapped_column(String(500), nullable=True)
    preferred_employment_types: Mapped[str | None] = mapped_column(String(300), nullable=True)
    resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="VISIBLE")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
