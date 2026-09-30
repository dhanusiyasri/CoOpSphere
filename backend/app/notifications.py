from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.users.models import User
from app.training.models import Enrollment, Nomination, TrainingBatch, TrainingProgramme, TrainingCourse, CourseLesson
from app.training.schedule_models import TrainingSchedule
from app.attendance.models import AttendanceRecord, AttendanceSession
from app.lms.models import LessonProgress, AssessmentAttempt
from app.credentials.models import Credential
from app.careers.models import JobApplication, JobPosting, EmploymentOutcome

router = APIRouter(prefix="/notifications", tags=["Notifications"])
MANAGERS = {"NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER"}


def _n(kind, title, message, priority="INFO", action=None):
    return {"id": f"{kind}:{title}:{action or ''}", "kind": kind, "title": title, "message": message, "priority": priority, "action": action}


def _manager_batch_filter(query, user):
    if user.role == "TRAINER":
        return query.where(TrainingBatch.trainer_id == user.id)
    if user.role == "INSTITUTE_ADMIN":
        return query.join(TrainingProgramme, TrainingProgramme.id == TrainingBatch.programme_id).where(
            TrainingProgramme.institution_id == user.institution_id
        )
    return query


@router.get("", response_model=list[dict])
def notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    out = []
    today = date.today()

    if user.role == "TRAINEE":
        active_enrollments = db.scalars(select(Enrollment).where(Enrollment.trainee_id == user.id, Enrollment.status == "ACTIVE")).all()
        batch_ids = [e.batch_id for e in active_enrollments]

        # Upcoming sessions in the next 7 days.
        if batch_ids:
            sessions = db.scalars(select(TrainingSchedule).where(
                TrainingSchedule.batch_id.in_(batch_ids),
                TrainingSchedule.session_date >= today,
                TrainingSchedule.session_date <= today + timedelta(days=7),
                TrainingSchedule.status != "CANCELLED",
            ).order_by(TrainingSchedule.session_date, TrainingSchedule.start_time).limit(5)).all()
            for s in sessions:
                out.append(_n("SESSION", "Upcoming training session", f"{s.topic} is scheduled for {s.session_date} at {s.start_time.strftime('%H:%M')}.", "INFO", "Training Evaluation"))

            # Low attendance using session/active enrollment records.
            attendance_sessions = db.scalars(select(AttendanceSession).where(AttendanceSession.batch_id.in_(batch_ids))).all()
            if attendance_sessions:
                records = db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id.in_([s.id for s in attendance_sessions]), AttendanceRecord.trainee_id == user.id)).all()
                present = sum(1 for r in records if r.status in {"PRESENT", "LATE"})
                rate = (present / len(attendance_sessions)) * 100
                if rate < 75:
                    out.append(_n("ATTENDANCE", "Attendance needs attention", f"Your attendance is {rate:.0f}%, below the 75% advisory threshold.", "HIGH", "Attendance"))

        incomplete = db.scalar(select(func.count()).select_from(LessonProgress).where(LessonProgress.trainee_id == user.id, LessonProgress.status != "COMPLETED")) or 0
        if incomplete:
            out.append(_n("LEARNING", "Learning progress pending", f"You have {incomplete} lesson progress record(s) still incomplete.", "MEDIUM", "LMS"))

        credentials = db.scalar(select(func.count()).select_from(Credential).where(Credential.trainee_id == user.id, Credential.status == "ISSUED")) or 0
        if credentials == 0:
            out.append(_n("CREDENTIAL", "No issued credential yet", "Complete eligible learning and assessments to become credential-ready.", "INFO", "Skills & Credentials"))

        apps = db.scalars(select(JobApplication).where(JobApplication.trainee_id == user.id).order_by(JobApplication.applied_at.desc()).limit(5)).all()
        for a in apps:
            if a.status in {"INTERVIEW", "SELECTED"}:
                out.append(_n("CAREER", f"Application: {a.status.replace('_', ' ')}", f"Your application #{a.id} is currently {a.status.replace('_', ' ').lower()}.", "HIGH" if a.status == "INTERVIEW" else "INFO", "Careers"))

        out.sort(key=lambda x: (x["priority"] != "HIGH", x["priority"] != "MEDIUM", x["title"]))
        return out[:12]

    if user.role in MANAGERS:
        # Pending nominations.
        nq = select(func.count()).select_from(Nomination).join(TrainingBatch, TrainingBatch.id == Nomination.batch_id).where(Nomination.status == "SUBMITTED")
        nq = _manager_batch_filter(nq, user)
        pending_nom = db.scalar(nq) or 0
        if pending_nom:
            out.append(_n("NOMINATION", "Nomination approvals pending", f"{pending_nom} nomination(s) are waiting for review.", "HIGH", "Training ERP"))

        # Upcoming sessions.
        sq = select(TrainingSchedule).join(TrainingBatch, TrainingBatch.id == TrainingSchedule.batch_id).where(
            TrainingSchedule.session_date >= today,
            TrainingSchedule.session_date <= today + timedelta(days=3),
            TrainingSchedule.status != "CANCELLED",
        )
        sq = _manager_batch_filter(sq, user)
        upcoming = db.scalars(sq.order_by(TrainingSchedule.session_date, TrainingSchedule.start_time).limit(5)).all()
        for s in upcoming:
            out.append(_n("SESSION", "Upcoming training session", f"{s.topic} is scheduled for {s.session_date} at {s.start_time.strftime('%H:%M')}.", "INFO", "Training Logistics"))

        # Low attendance count for visible batches.
        bq = _manager_batch_filter(select(TrainingBatch), user)
        batches = db.scalars(bq).all()
        batch_ids = [b.id for b in batches]
        low = 0
        if batch_ids:
            sessions = db.scalars(select(AttendanceSession).where(AttendanceSession.batch_id.in_(batch_ids))).all()
            if sessions:
                enrollments = db.scalars(select(Enrollment).where(Enrollment.batch_id.in_(batch_ids), Enrollment.status == "ACTIVE")).all()
                recs = db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id.in_([s.id for s in sessions]))).all()
                by = {}
                for e in enrollments:
                    by[e.trainee_id] = [0, 0]
                session_batch = {s.id: s.batch_id for s in sessions}
                for e in enrollments:
                    for s in sessions:
                        if s.batch_id == e.batch_id:
                            by.setdefault(e.trainee_id, [0, 0])[1] += 1
                for r in recs:
                    if r.trainee_id in by and r.status in {"PRESENT", "LATE"}:
                        by[r.trainee_id][0] += 1
                low = sum(1 for p, total in by.values() if total and (p / total) * 100 < 75)
        if low:
            out.append(_n("ATTENDANCE", "Low-attendance trainees", f"{low} trainee(s) are below the 75% advisory attendance threshold.", "HIGH", "Attendance"))

        placement_q = select(func.count()).select_from(EmploymentOutcome).where(EmploymentOutcome.status == "PENDING_JOINING")
        pending_joining = db.scalar(placement_q) or 0
        if pending_joining:
            out.append(_n("PLACEMENT", "Placements awaiting joining", f"{pending_joining} accepted placement(s) are awaiting joining confirmation.", "MEDIUM", "Careers"))

        out.append(_n("SYSTEM", "Action Center ready", "Use this panel to jump directly to items that need attention.", "INFO", "Notifications"))
        return out[:12]

    return [_n("SYSTEM", "No alerts", "There are no role-specific action alerts yet.", "INFO", "Notifications")]
