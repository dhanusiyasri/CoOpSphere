from pydantic import BaseModel


class IntelligenceOverview(BaseModel):
    trainees: int
    programmes: int
    batches: int
    active_enrollments: int
    courses: int
    lessons: int
    completed_lesson_records: int
    lesson_activity_rate: int
    assessment_attempts: int
    assessment_passes: int
    assessment_pass_rate: int
    credentials_issued: int
    published_jobs: int
    job_applications: int
    selected_applications: int
    placement_conversion_rate: int
    application_statuses: dict[str, int]
    programme_summary: list[dict[str, object]]


class IntelligenceInstitutionSummary(BaseModel):
    id: int
    name: str
    institution_type: str
    state: str | None
    district: str | None
    programme_count: int
    batch_count: int
    trainee_count: int
    active_enrollment_count: int


class IntelligenceTrainerSummary(BaseModel):
    id: int
    full_name: str
    email: str
    institution_id: int | None
    batch_count: int
    active_batch_count: int
    trainee_count: int


class IntelligenceProgrammeDetail(BaseModel):
    id: int
    code: str
    title: str
    description: str | None
    category: str
    mode: str
    duration_days: int
    capacity: int
    status: str
    institution_name: str
    batch_count: int
    course_count: int
    trainee_count: int
    active_enrollment_count: int
    completed_lesson_records: int
    credential_count: int
    batches: list[dict[str, object]]
