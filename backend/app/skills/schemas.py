from datetime import datetime
from pydantic import BaseModel, Field

class DigitalLiteracyQuestion(BaseModel):
    id: str
    question: str
    options: list[str]

class DigitalLiteracyAttemptCreate(BaseModel):
    answers: dict[str, int]

class DigitalLiteracyAttemptResponse(BaseModel):
    id: int
    trainee_id: int
    trainee_name: str
    trainee_email: str
    score: int
    total_questions: int
    percentage: int
    level: str
    completed_at: datetime

class DigitalLiteracyResult(BaseModel):
    score: int
    total_questions: int
    percentage: int
    level: str
    completed_at: datetime
