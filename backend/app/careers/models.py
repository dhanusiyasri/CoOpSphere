from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class JobPosting(Base):
    __tablename__ = "career_job_postings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    organization_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(160), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(40), nullable=False, default="FULL_TIME")
    skills: Mapped[str | None] = mapped_column(String(500), nullable=True)
    minimum_education: Mapped[str | None] = mapped_column(String(120), nullable=True)
    minimum_experience_years: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    salary_range: Mapped[str | None] = mapped_column(String(120), nullable=True)
    closing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class JobApplication(Base):
    __tablename__ = "career_job_applications"
    __table_args__ = (
        UniqueConstraint("job_id", "trainee_id", name="uq_career_job_application_job_trainee"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("career_job_postings.id", ondelete="CASCADE"), nullable=False, index=True)
    trainee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="APPLIED")
    cover_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    interview_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    interview_mode: Mapped[str | None] = mapped_column(String(30), nullable=True)
    interview_location_or_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    interview_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    offer_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    offer_offered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    offer_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    offer_salary: Mapped[str | None] = mapped_column(String(120), nullable=True)
    offer_employment_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    offer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    offer_responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EmploymentOutcome(Base):
    __tablename__ = "career_employment_outcomes"
    __table_args__ = (UniqueConstraint("application_id", name="uq_career_employment_outcome_application"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("career_job_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    trainee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING_JOINING")
    joining_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class EmploymentFollowUp(Base):
    __tablename__ = "career_employment_followups"
    __table_args__ = (UniqueConstraint("placement_id", "checkpoint", name="uq_career_followup_placement_checkpoint"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    placement_id: Mapped[int] = mapped_column(ForeignKey("career_employment_outcomes.id", ondelete="CASCADE"), nullable=False, index=True)
    trainee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    checkpoint: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="CONTINUING")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    employer_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    trainee_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
