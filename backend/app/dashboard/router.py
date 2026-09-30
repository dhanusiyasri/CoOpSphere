from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.careers.models import JobApplication, JobPosting
from app.credentials.models import Credential
from app.lms.models import AssessmentAttempt, LessonProgress
from app.training.models import CourseLesson, Enrollment, TrainingBatch, TrainingCourse, TrainingProgramme
from app.users.models import User
from app.attendance.models import AttendanceRecord, AttendanceSession

from app.dashboard.schemas import DashboardAttendance, DashboardItem, DashboardMetric, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
ATTENDANCE_THRESHOLD = 75.0
MANAGER_ROLES = {"NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER"}


def metric(label: str, value: int, detail: str) -> DashboardMetric:
    return DashboardMetric(label=label, value=value, detail=detail)


def item(label: str, value: str, detail: str | None = None) -> DashboardItem:
    return DashboardItem(label=label, value=value, detail=detail)


def _attendance_dashboard(db: Session, user: User) -> DashboardAttendance | None:
    if user.role not in MANAGER_ROLES and user.role != "TRAINEE":
        return None

    query = (
        select(AttendanceSession, TrainingBatch)
        .join(TrainingBatch, TrainingBatch.id == AttendanceSession.batch_id)
        .order_by(AttendanceSession.session_date.desc(), AttendanceSession.start_time.desc())
    )
    if user.role == "TRAINER":
        query = query.where(TrainingBatch.trainer_id == user.id)
    elif user.role == "INSTITUTE_ADMIN":
        query = query.join(
            TrainingProgramme, TrainingProgramme.id == TrainingBatch.programme_id
        ).where(TrainingProgramme.institution_id == user.institution_id)

    if user.role == "TRAINEE":
        query = query.join(
            Enrollment,
            (Enrollment.batch_id == AttendanceSession.batch_id)
            & (Enrollment.trainee_id == user.id),
        ).where(Enrollment.status == "ACTIVE")

    rows = db.execute(query).all()
    if not rows:
        return DashboardAttendance(
            attendance_rate=0.0,
            total_sessions=0,
            present=0,
            late=0,
            absent=0,
            low_attendance_count=0,
            threshold=ATTENDANCE_THRESHOLD,
        )

    session_ids = [session.id for session, _batch in rows]
    records = db.scalars(
        select(AttendanceRecord).where(AttendanceRecord.session_id.in_(session_ids))
    ).all()
    record_by_key = {(record.session_id, record.trainee_id): record for record in records}

    if user.role == "TRAINEE":
        present = late = absent = 0
        for session, _batch in rows:
            record = record_by_key.get((session.id, user.id))
            status_value = record.status if record else "ABSENT"
            if status_value == "PRESENT":
                present += 1
            elif status_value == "LATE":
                late += 1
            else:
                absent += 1
        total_sessions = len(rows)
        rate = round(((present + late) / total_sessions) * 100, 1) if total_sessions else 0.0
        return DashboardAttendance(
            attendance_rate=rate,
            total_sessions=total_sessions,
            present=present,
            late=late,
            absent=absent,
            low_attendance_count=1 if total_sessions and rate < ATTENDANCE_THRESHOLD else 0,
            threshold=ATTENDANCE_THRESHOLD,
        )

    batch_ids = sorted({session.batch_id for session, _batch in rows})
    enrollments = db.scalars(
        select(Enrollment).where(
            Enrollment.batch_id.in_(batch_ids),
            Enrollment.status == "ACTIVE",
        )
    ).all() if batch_ids else []
    enrollments_by_batch: dict[int, list[Enrollment]] = {}
    for enrollment in enrollments:
        enrollments_by_batch.setdefault(enrollment.batch_id, []).append(enrollment)

    present = late = absent = 0
    trainee_acc: dict[int, dict[str, int]] = {}
    for session, batch in rows:
        for enrollment in enrollments_by_batch.get(batch.id, []):
            record = record_by_key.get((session.id, enrollment.trainee_id))
            status_value = record.status if record else "ABSENT"
            if status_value == "PRESENT":
                present += 1
            elif status_value == "LATE":
                late += 1
            else:
                absent += 1
            acc = trainee_acc.setdefault(
                enrollment.trainee_id,
                {"sessions": 0, "present": 0, "late": 0},
            )
            acc["sessions"] += 1
            if status_value == "PRESENT":
                acc["present"] += 1
            elif status_value == "LATE":
                acc["late"] += 1

    attendance_slots = sum(value["sessions"] for value in trainee_acc.values())
    rate = round(((present + late) / attendance_slots) * 100, 1) if attendance_slots else 0.0
    low_count = 0
    for value in trainee_acc.values():
        trainee_rate = ((value["present"] + value["late"]) / value["sessions"]) * 100 if value["sessions"] else 0
        if trainee_rate < ATTENDANCE_THRESHOLD:
            low_count += 1

    return DashboardAttendance(
        attendance_rate=rate,
        total_sessions=len(rows),
        present=present,
        late=late,
        absent=absent,
        low_attendance_count=low_count,
        threshold=ATTENDANCE_THRESHOLD,
    )


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    attendance = _attendance_dashboard(db, user)

    if user.role == "TRAINEE":
        active = db.scalar(
            select(func.count()).select_from(Enrollment).where(
                Enrollment.trainee_id == user.id, Enrollment.status == "ACTIVE"
            )
        ) or 0
        credential_count = db.scalar(
            select(func.count()).select_from(Credential).where(Credential.trainee_id == user.id)
        ) or 0
        completed = db.scalar(
            select(func.count()).select_from(LessonProgress).where(
                LessonProgress.trainee_id == user.id, LessonProgress.status == "COMPLETED"
            )
        ) or 0
        attempts = db.scalar(
            select(func.count()).select_from(AssessmentAttempt).where(AssessmentAttempt.trainee_id == user.id)
        ) or 0
        applications = db.scalar(
            select(func.count()).select_from(JobApplication).where(JobApplication.trainee_id == user.id)
        ) or 0
        selected = db.scalar(
            select(func.count()).select_from(JobApplication).where(
                JobApplication.trainee_id == user.id, JobApplication.status == "SELECTED"
            )
        ) or 0
        recent_credentials = db.execute(
            select(Credential).where(Credential.trainee_id == user.id).order_by(Credential.issued_at.desc()).limit(5)
        ).scalars().all()
        recent_apps = db.execute(
            select(JobApplication, JobPosting)
            .join(JobPosting, JobPosting.id == JobApplication.job_id)
            .where(JobApplication.trainee_id == user.id)
            .order_by(JobApplication.applied_at.desc()).limit(5)
        ).all()
        items = [
            *[item(c.course_title, c.credential_number, f"Credential issued {c.issued_at.date().isoformat()}") for c in recent_credentials],
            *[item(j.title, a.status, j.organization_name) for a, j in recent_apps],
        ]
        return DashboardSummary(
            role=user.role,
            heading=f"Welcome back, {user.full_name}",
            subtitle="Your training, credentials and employment activity in one place.",
            metrics=[
                metric("Active enrolments", active, "Current training enrolments"),
                metric("Lessons completed", completed, "Persisted LMS completions"),
                metric("Credentials", credential_count, "Issued NCCT credentials"),
                metric("Applications", applications, f"{selected} selected"),
            ],
            items=items,
            attendance=attendance,
        )

    if user.role == "EMPLOYER":
        jobs = db.scalar(select(func.count()).select_from(JobPosting).where(JobPosting.employer_id == user.id)) or 0
        published = db.scalar(
            select(func.count()).select_from(JobPosting).where(JobPosting.employer_id == user.id, JobPosting.status == "PUBLISHED")
        ) or 0
        applications = db.scalar(
            select(func.count()).select_from(JobApplication).join(JobPosting, JobPosting.id == JobApplication.job_id).where(JobPosting.employer_id == user.id)
        ) or 0
        selected = db.scalar(
            select(func.count()).select_from(JobApplication).join(JobPosting, JobPosting.id == JobApplication.job_id).where(JobPosting.employer_id == user.id, JobApplication.status == "SELECTED")
        ) or 0
        rows = db.execute(
            select(JobPosting.title, JobPosting.status, func.count(JobApplication.id).label("applications"))
            .outerjoin(JobApplication, JobApplication.job_id == JobPosting.id)
            .where(JobPosting.employer_id == user.id)
            .group_by(JobPosting.id, JobPosting.title, JobPosting.status)
            .order_by(JobPosting.created_at.desc()).limit(8)
        ).all()
        return DashboardSummary(
            role=user.role,
            heading=f"Employer workspace, {user.full_name}",
            subtitle="Track published opportunities and candidate applications.",
            metrics=[
                metric("Your jobs", jobs, f"{published} published"),
                metric("Applications", applications, "Across your jobs"),
                metric("Selected", selected, "Applications marked selected"),
                metric("Open opportunities", published, "Currently published"),
            ],
            items=[item(r.title, r.status, f"{r.applications} applications") for r in rows],
            attendance=None,
        )

    trainees = db.scalar(select(func.count()).select_from(User).where(User.role == "TRAINEE")) or 0
    programmes = db.scalar(select(func.count()).select_from(TrainingProgramme)) or 0
    batches = db.scalar(select(func.count()).select_from(TrainingBatch)) or 0
    active_enrollments = db.scalar(
        select(func.count()).select_from(Enrollment).where(Enrollment.status == "ACTIVE")
    ) or 0
    courses = db.scalar(select(func.count()).select_from(TrainingCourse)) or 0
    credentials = db.scalar(select(func.count()).select_from(Credential)) or 0
    published_jobs = db.scalar(
        select(func.count()).select_from(JobPosting).where(JobPosting.status == "PUBLISHED")
    ) or 0
    applications = db.scalar(select(func.count()).select_from(JobApplication)) or 0
    completed = db.scalar(select(func.count()).select_from(LessonProgress).where(LessonProgress.status == "COMPLETED")) or 0
    lessons = db.scalar(select(func.count()).select_from(CourseLesson)) or 0
    lesson_rate = round((completed / lessons) * 100) if lessons else 0
    return DashboardSummary(
        role=user.role,
        heading="NCCT operational dashboard",
        subtitle="Central view across training, learning, credentials and employment activity.",
        metrics=[
            metric("Trainees", trainees, "Registered trainee accounts"),
            metric("Programmes", programmes, "Training programmes"),
            metric("Batches", batches, "Configured training batches"),
            metric("Active enrolments", active_enrollments, "Current active enrolments"),
            metric("Courses", courses, "Configured LMS courses"),
            metric("Credentials", credentials, "Issued credentials"),
            metric("Published jobs", published_jobs, "Employment exchange"),
            metric("Lesson completion", lesson_rate, f"{completed} of {lessons} lesson records"),
        ],
        items=[
            item("Training ERP", f"{programmes} programmes", f"{batches} batches"),
            item("LMS", f"{courses} courses", f"{lesson_rate}% lesson completion rate"),
            item("Credentials", str(credentials), "Issued NCCT credentials"),
            item("Employment", f"{published_jobs} published jobs", f"{applications} applications"),
        ],
        attendance=attendance,
    )
