from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CareerProfileUpdate(BaseModel):
    headline: str | None = Field(default=None, max_length=160)
    professional_summary: str | None = None
    skills: str | None = Field(default=None, max_length=1000)
    preferred_locations: str | None = Field(default=None, max_length=500)
    preferred_employment_types: str | None = Field(default=None, max_length=300)
    resume_text: str | None = None
    profile_visibility: str = Field(default="VISIBLE", pattern="^(VISIBLE|HIDDEN)$")


class CareerProfileResponse(CareerProfileUpdate):
    id: int
    trainee_id: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RecommendedJobResponse(BaseModel):
    job_id: int
    title: str
    organization_name: str
    location: str
    employment_type: str
    skills: str | None
    minimum_education: str | None
    minimum_experience_years: int
    salary_range: str | None
    match_score: int
    matched_skills: list[str]
    reasons: list[str]


class CandidateProfileResponse(BaseModel):
    trainee_id: int
    full_name: str
    email: str
    participant_code: str | None
    phone: str | None
    designation: str | None
    organization_name: str | None
    education_level: str | None
    district: str | None
    state: str | None
    digital_literacy_level: str | None
    years_experience: int
    headline: str | None
    professional_summary: str | None
    skills: str | None
    preferred_locations: str | None
    preferred_employment_types: str | None
    resume_text: str | None

class CandidateSearchResponse(BaseModel):
    trainee_id: int
    full_name: str
    headline: str | None
    email: str
    phone: str | None
    education_level: str | None
    years_experience: int
    district: str | None
    state: str | None
    skills: str | None
    digital_literacy_level: str | None
    credential_count: int
    profile_visibility: str

