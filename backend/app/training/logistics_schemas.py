from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class LogisticsPlanCreate(BaseModel):
    batch_id: int
    hostel_required: bool = False
    hostel_name: str | None = Field(default=None, max_length=200)
    rooms_available: int = Field(default=0, ge=0)
    meals_included: bool = False
    meal_notes: str | None = Field(default=None, max_length=500)
    transport_required: bool = False
    pickup_point: str | None = Field(default=None, max_length=300)
    transport_notes: str | None = Field(default=None, max_length=500)
    coordinator_name: str | None = Field(default=None, max_length=150)
    coordinator_phone: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)

class LogisticsPlanResponse(LogisticsPlanCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    batch_code: str
    programme_title: str
    allocated_count: int
    created_by_id: int
    created_at: datetime


class EligibleTraineeResponse(BaseModel):
    trainee_id: int
    full_name: str
    email: str
    enrollment_id: int
    enrollment_status: str

class AccommodationCreate(BaseModel):
    batch_id: int
    trainee_id: int
    room_number: str = Field(min_length=1, max_length=50)
    bed_number: str | None = Field(default=None, max_length=50)
    status: str = Field(default="ALLOCATED", max_length=30)
    notes: str | None = Field(default=None, max_length=2000)

class AccommodationResponse(AccommodationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trainee_name: str
    trainee_email: str
    allocated_by_id: int
    allocated_at: datetime
