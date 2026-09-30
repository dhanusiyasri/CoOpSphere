from pydantic import BaseModel


class DashboardMetric(BaseModel):
    label: str
    value: int
    detail: str


class DashboardItem(BaseModel):
    label: str
    value: str
    detail: str | None = None


class DashboardAttendance(BaseModel):
    attendance_rate: float
    total_sessions: int
    present: int
    late: int
    absent: int
    low_attendance_count: int
    threshold: float


class DashboardSummary(BaseModel):
    role: str
    heading: str
    subtitle: str
    metrics: list[DashboardMetric]
    items: list[DashboardItem]
    attendance: DashboardAttendance | None = None
