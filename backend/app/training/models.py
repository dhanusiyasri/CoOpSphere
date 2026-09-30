from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TrainingProgramme(Base):
    __tablename__ = "training_programmes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[str] = mapped_column(String(40), nullable=False, default="HYBRID")
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    batches: Mapped[list["TrainingBatch"]] = relationship(back_populates="programme", cascade="all, delete-orphan")


class TrainingBatch(Base):
    __tablename__ = "training_batches"
    __table_args__ = (UniqueConstraint("programme_id", "batch_code", name="uq_batch_programme_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    programme_id: Mapped[int] = mapped_column(ForeignKey("training_programmes.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_code: Mapped[str] = mapped_column(String(60), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    trainer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    venue: Mapped[str | None] = mapped_column(String(200), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PLANNED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    programme: Mapped[TrainingProgramme] = relationship(back_populates="batches")


class Nomination(Base):
    __tablename__ = "training_nominations"
    __table_args__ = (UniqueConstraint("batch_id", "trainee_id", name="uq_nomination_batch_trainee"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("training_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    trainee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    nominated_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="SUBMITTED")
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ParticipantProfile(Base):
    __tablename__ = "training_participant_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    participant_code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    participant_type: Mapped[str] = mapped_column(String(50), nullable=False, default="RURAL_YOUTH")
    designation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    organization_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    digital_literacy_level: Mapped[str] = mapped_column(String(30), nullable=False, default="BASIC")
    years_experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    profile_status: Mapped[str] = mapped_column(String(30), nullable=False, default="INCOMPLETE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Enrollment(Base):
    __tablename__ = "training_enrollments"
    __table_args__ = (UniqueConstraint("batch_id", "trainee_id", name="uq_enrollment_batch_trainee"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("training_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    trainee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    nomination_id: Mapped[int | None] = mapped_column(ForeignKey("training_nominations.id", ondelete="SET NULL"), nullable=True, unique=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TrainingCourse(Base):
    __tablename__ = "training_courses"
    __table_args__ = (UniqueConstraint("programme_id", "course_code", name="uq_course_programme_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    programme_id: Mapped[int] = mapped_column(ForeignKey("training_programmes.id", ondelete="CASCADE"), nullable=False, index=True)
    course_code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="GENERAL")
    delivery_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="HYBRID")
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    level: Mapped[str] = mapped_column(String(30), nullable=False, default="FOUNDATION")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CourseModule(Base):
    __tablename__ = "training_course_modules"
    __table_args__ = (UniqueConstraint("course_id", "module_number", name="uq_course_module_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("training_courses.id", ondelete="CASCADE"), nullable=False, index=True)
    module_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    learning_objectives: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CourseLesson(Base):
    __tablename__ = "training_course_lessons"
    __table_args__ = (UniqueConstraint("module_id", "lesson_number", name="uq_module_lesson_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("training_course_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content_type: Mapped[str] = mapped_column(String(30), nullable=False, default="TEXT")
    content_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    is_mandatory: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
