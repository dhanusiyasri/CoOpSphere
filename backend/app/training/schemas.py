from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProgrammeCreate(BaseModel):
    institution_id: int
    code: str = Field(min_length=2, max_length=40)
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    category: str = Field(min_length=2, max_length=100)
    mode: str = Field(default="HYBRID", max_length=40)
    duration_days: int = Field(default=1, ge=1)
    capacity: int = Field(default=30, ge=1)
    status: str = Field(default="DRAFT", max_length=30)


class ProgrammeResponse(ProgrammeCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class BatchCreate(BaseModel):
    programme_id: int
    batch_code: str = Field(min_length=2, max_length=60)
    start_date: date
    end_date: date
    trainer_id: int | None = None
    venue: str | None = Field(default=None, max_length=200)
    capacity: int = Field(default=30, ge=1)
    status: str = Field(default="PLANNED", max_length=30)


class BatchResponse(BatchCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class NominationCreate(BaseModel):
    batch_id: int
    trainee_id: int
    remarks: str | None = Field(default=None, max_length=1000)


class NominationDecision(BaseModel):
    remarks: str | None = Field(default=None, max_length=1000)


class NominationResponse(NominationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nominated_by_id: int
    status: str
    created_at: datetime


class EnrollmentCreate(BaseModel):
    batch_id: int
    trainee_id: int
    nomination_id: int | None = None


class EnrollmentResponse(EnrollmentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    enrolled_at: datetime


class ParticipantProfileCreate(BaseModel):
    user_id: int
    participant_code: str = Field(min_length=2, max_length=40)
    phone: str | None = Field(default=None, max_length=30)
    participant_type: str = Field(default="RURAL_YOUTH", max_length=50)
    designation: str | None = Field(default=None, max_length=120)
    organization_name: str | None = Field(default=None, max_length=200)
    education_level: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    digital_literacy_level: str = Field(default="BASIC", max_length=30)
    years_experience: int = Field(default=0, ge=0, le=60)
    profile_status: str = Field(default="INCOMPLETE", max_length=30)


class ParticipantProfileResponse(ParticipantProfileCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_full_name: str
    user_email: str
    created_at: datetime
    updated_at: datetime


class CourseCreate(BaseModel):
    programme_id: int
    course_code: str = Field(min_length=2, max_length=50)
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    category: str = Field(default="GENERAL", max_length=100)
    delivery_mode: str = Field(default="HYBRID", max_length=30)
    duration_hours: int = Field(default=4, ge=1, le=1000)
    level: str = Field(default="FOUNDATION", max_length=30)
    status: str = Field(default="DRAFT", max_length=30)

class CourseResponse(CourseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

class CourseModuleCreate(BaseModel):
    course_id: int
    module_number: int = Field(ge=1)
    title: str = Field(min_length=2, max_length=200)
    learning_objectives: str | None = None
    duration_minutes: int = Field(default=60, ge=1, le=10000)

class CourseModuleResponse(CourseModuleCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

class CourseLessonCreate(BaseModel):
    module_id: int
    lesson_number: int = Field(ge=1)
    title: str = Field(min_length=2, max_length=200)
    content_type: str = Field(default="TEXT", max_length=30)
    content_url: str | None = Field(default=None, max_length=500)
    duration_minutes: int = Field(default=15, ge=1, le=10000)
    is_mandatory: bool = True

class CourseLessonResponse(CourseLessonCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
