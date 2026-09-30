from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field


class ScheduleCreate(BaseModel):
    batch_id: int
    course_id: int | None = None
    module_id: int | None = None
    trainer_id: int | None = None
    session_date: date
    start_time: time
    end_time: time
    topic: str = Field(min_length=2, max_length=200)
    venue: str | None = Field(default=None, max_length=200)
    mode: str = Field(default="IN_PERSON", max_length=30)
    status: str = Field(default="SCHEDULED", max_length=30)
    notes: str | None = Field(default=None, max_length=2000)


class ScheduleResponse(ScheduleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    attendance_session_id: int | None
    created_by_id: int
    created_at: datetime
    batch_code: str
    programme_title: str
    course_title: str | None = None
    module_title: str | None = None
    trainer_name: str | None = None


class ScheduleAttendanceResponse(BaseModel):
    schedule_id: int
    attendance_session_id: int
    access_code: str
