from datetime import date, datetime, time
from pydantic import BaseModel, ConfigDict, Field


class AttendanceSessionCreate(BaseModel):
    batch_id: int
    session_date: date
    start_time: time
    end_time: time
    topic: str = Field(min_length=2, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    status: str = Field(default="SCHEDULED", max_length=20)


class AttendanceSessionResponse(AttendanceSessionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    access_code: str
    created_by_id: int
    created_at: datetime


class AttendanceRecordUpdate(BaseModel):
    trainee_id: int
    status: str = Field(default="PRESENT", max_length=20)
    remarks: str | None = Field(default=None, max_length=500)


class AttendanceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: int
    trainee_id: int
    status: str
    method: str
    check_in_at: datetime | None
    marked_by_id: int | None
    remarks: str | None
    trainee_name: str
    trainee_email: str


class AttendanceCheckIn(BaseModel):
    access_code: str = Field(min_length=4, max_length=20)


class AttendanceQrResponse(BaseModel):
    session_id: int
    access_code: str
    data_url: str


class AttendanceReportSession(BaseModel):
    session_id: int
    batch_id: int
    batch_code: str
    session_date: date
    start_time: time
    end_time: time
    topic: str
    status: str
    roster_count: int
    present: int
    late: int
    absent: int
    excused: int
    attendance_rate: float


class AttendanceReportTrainee(BaseModel):
    trainee_id: int
    trainee_name: str
    trainee_email: str
    total_sessions: int
    present: int
    late: int
    absent: int
    excused: int
    attendance_rate: float
    last_check_in_at: datetime | None


class AttendanceReportBatch(BaseModel):
    batch_id: int
    batch_code: str
    total_sessions: int
    enrolled_trainees: int
    attendance_slots: int
    present: int
    late: int
    absent: int
    excused: int
    attendance_rate: float


class AttendanceReportSummary(BaseModel):
    total_sessions: int
    enrolled_trainees: int
    attendance_slots: int
    present: int
    late: int
    absent: int
    excused: int
    attendance_rate: float
    qr_checkins: int
    manual_marks: int
    exceptions: int


class AttendanceReportResponse(BaseModel):
    from_date: date | None
    to_date: date | None
    batch_id: int | None
    summary: AttendanceReportSummary
    batches: list[AttendanceReportBatch]
    sessions: list[AttendanceReportSession]
    trainees: list[AttendanceReportTrainee]


class LowAttendanceAlert(BaseModel):
    trainee_id: int
    trainee_name: str
    trainee_email: str
    batch_id: int
    batch_code: str
    total_sessions: int
    present: int
    late: int
    absent: int
    excused: int
    attendance_rate: float
    threshold: float


class LowAttendanceAlertResponse(BaseModel):
    threshold: float
    alerts: list[LowAttendanceAlert]
