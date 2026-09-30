from datetime import datetime

from pydantic import BaseModel, Field


class LessonProgressResponse(BaseModel):
    id: int
    trainee_id: int
    lesson_id: int
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    last_accessed_at: datetime | None
    model_config = {"from_attributes": True}


class LessonResponse(BaseModel):
    id: int
    module_id: int
    lesson_number: int
    title: str
    content_type: str
    content_url: str | None
    duration_minutes: int
    is_mandatory: bool
    status: str
    assessment_id: int | None = None
    assessment_title: str | None = None
    assessment_question_count: int = 0
    assessment_pass_mark: int | None = None
    model_config = {"from_attributes": True}


class ModuleResponse(BaseModel):
    id: int
    course_id: int
    module_number: int
    title: str
    learning_objectives: str | None
    duration_minutes: int
    lessons: list[LessonResponse]
    model_config = {"from_attributes": True}


class CourseDetailResponse(BaseModel):
    id: int
    programme_id: int
    course_code: str
    title: str
    description: str | None
    category: str
    delivery_mode: str
    duration_hours: int
    level: str
    status: str
    modules: list[ModuleResponse]
    total_lessons: int
    completed_lessons: int
    progress_percent: int


class MyCourseResponse(BaseModel):
    course_id: int
    course_code: str
    title: str
    programme_id: int
    total_lessons: int
    completed_lessons: int
    progress_percent: int


class AssessmentOptionResponse(BaseModel):
    id: int
    option_number: int
    option_text: str


class AssessmentQuestionResponse(BaseModel):
    id: int
    question_number: int
    question_text: str
    marks: int
    options: list[AssessmentOptionResponse]


class AssessmentResponse(BaseModel):
    id: int
    lesson_id: int
    title: str
    instructions: str | None
    pass_mark: int
    max_attempts: int
    status: str
    question_count: int
    max_score: int
    questions: list[AssessmentQuestionResponse]


class AssessmentAnswerInput(BaseModel):
    question_id: int
    selected_option_id: int | None = None


class AssessmentSubmitRequest(BaseModel):
    answers: list[AssessmentAnswerInput] = Field(default_factory=list)


class AssessmentAttemptResponse(BaseModel):
    id: int
    assessment_id: int
    trainee_id: int
    attempt_number: int
    score: int
    max_score: int
    percentage: int
    result: str
    submitted_at: datetime
    model_config = {"from_attributes": True}
