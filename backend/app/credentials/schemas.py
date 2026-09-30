from datetime import datetime

from pydantic import BaseModel


class CredentialResponse(BaseModel):
    id: int
    trainee_id: int
    course_id: int
    credential_number: str
    title: str
    course_title: str
    status: str
    score_percentage: int
    completed_lessons: int
    total_lessons: int
    issued_at: datetime
    model_config = {"from_attributes": True}


class CredentialEligibilityResponse(BaseModel):
    course_id: int
    eligible: bool
    total_lessons: int
    completed_lessons: int
    score_percentage: int
    reason: str | None = None


class CredentialVerificationResponse(BaseModel):
    valid: bool
    credential_number: str
    title: str
    course_title: str
    trainee_name: str
    score_percentage: int
    completed_lessons: int
    total_lessons: int
    issued_at: datetime
    status: str
    revoked_at: datetime | None = None
    revocation_reason: str | None = None


class CredentialRegistryResponse(CredentialResponse):
    trainee_name: str
    trainee_email: str
    institution_id: int | None = None
    institution_name: str | None = None
    revoked_at: datetime | None = None
    revoked_by_id: int | None = None
    issued_by_id: int | None = None
    revocation_reason: str | None = None


class CredentialRevokeRequest(BaseModel):
    reason: str


class CredentialReadinessResponse(BaseModel):
    trainee_id: int
    trainee_name: str
    trainee_email: str
    course_id: int
    course_code: str
    course_title: str
    batch_id: int
    batch_code: str
    lesson_completion_percent: int
    completed_lessons: int
    total_lessons: int
    assessment_passed: bool
    assessment_score: int
    attendance_percent: int | None = None
    attendance_threshold: int = 75
    eligible: bool
    reason: str | None = None
    credential_id: int | None = None
    credential_number: str | None = None
    credential_status: str | None = None
