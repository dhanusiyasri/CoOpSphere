from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class JobPostingCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    organization_name: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=10)
    location: str = Field(min_length=2, max_length=160)
    employment_type: str = "FULL_TIME"
    skills: str | None = None
    minimum_education: str | None = None
    minimum_experience_years: int = Field(default=0, ge=0)
    salary_range: str | None = None
    closing_date: date | None = None
    status: str = "PUBLISHED"


class JobPostingResponse(BaseModel):
    id: int
    employer_id: int
    title: str
    organization_name: str
    description: str
    location: str
    employment_type: str
    skills: str | None
    minimum_education: str | None
    minimum_experience_years: int
    salary_range: str | None
    closing_date: date | None
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class JobApplicationCreate(BaseModel):
    cover_note: str | None = Field(default=None, max_length=2000)


class JobApplicationResponse(BaseModel):
    id: int
    job_id: int
    trainee_id: int
    job_title: str
    organization_name: str
    status: str
    cover_note: str | None
    applied_at: datetime
    updated_at: datetime | None = None
    interview_scheduled_at: datetime | None = None
    interview_mode: str | None = None
    interview_location_or_link: str | None = None
    interview_notes: str | None = None
    offer_status: str | None = None
    offer_offered_at: datetime | None = None
    offer_expires_at: datetime | None = None
    offer_salary: str | None = None
    offer_employment_type: str | None = None
    offer_notes: str | None = None
    offer_responded_at: datetime | None = None


class ApplicationStatusUpdate(BaseModel):
    status: str


class InterviewScheduleRequest(BaseModel):
    scheduled_at: datetime
    mode: str = "ONLINE"
    location_or_link: str
    notes: str | None = None

class InterviewCancelRequest(BaseModel):
    reason: str | None = None


class OfferCreateRequest(BaseModel):
    expires_at: datetime | None = None
    salary: str | None = Field(default=None, max_length=120)
    employment_type: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=3000)


class OfferResponseRequest(BaseModel):
    decision: str


class PlacementUpdateRequest(BaseModel):
    status: str
    joining_date: date | None = None
    notes: str | None = Field(default=None, max_length=3000)


class PlacementResponse(BaseModel):
    id: int
    application_id: int
    trainee_id: int
    employer_id: int
    job_id: int
    job_title: str
    organization_name: str
    status: str
    joining_date: date | None
    notes: str | None
    updated_at: datetime


class PlacementSummary(BaseModel):
    total: int
    pending_joining: int
    joined: int
    not_joined: int


class PlacementAnalytics(BaseModel):
    jobs_total: int
    jobs_published: int
    applications_total: int
    applications_shortlisted: int
    applications_interview: int
    applications_selected: int
    applications_rejected: int
    offers_pending: int
    offers_accepted: int
    offers_declined: int
    placements_total: int
    pending_joining: int
    joined: int
    not_joined: int
    placement_join_rate: float


class EmploymentFollowUpRequest(BaseModel):
    checkpoint: str
    status: str = "CONTINUING"
    notes: str | None = Field(default=None, max_length=3000)
    employer_feedback: str | None = Field(default=None, max_length=3000)
    trainee_feedback: str | None = Field(default=None, max_length=3000)

class EmploymentFollowUpResponse(BaseModel):
    id: int
    placement_id: int
    trainee_id: int
    employer_id: int
    checkpoint: str
    status: str
    notes: str | None
    employer_feedback: str | None
    trainee_feedback: str | None
    checked_at: datetime
    updated_at: datetime
