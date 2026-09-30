from datetime import datetime
from pydantic import BaseModel, Field

class FeedbackCreate(BaseModel):
    schedule_id: int
    content_rating: int = Field(ge=1, le=5)
    trainer_rating: int = Field(ge=1, le=5)
    venue_rating: int = Field(ge=1, le=5)
    overall_rating: int = Field(ge=1, le=5)
    comments: str | None = None

class FeedbackResponse(FeedbackCreate):
    id: int
    batch_id: int
    trainee_id: int
    trainee_name: str
    submitted_at: datetime

class FeedbackSummary(BaseModel):
    schedule_id: int
    topic: str
    session_date: str
    batch_code: str
    responses: int
    average_content: float
    average_trainer: float
    average_venue: float
    average_overall: float
