from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.careers.models import JobApplication, JobPosting
from app.credentials.models import Credential
from app.institutions.models import Institution
from app.lms.models import AssessmentAttempt, LessonProgress
from app.training.models import CourseLesson, CourseModule, Enrollment, TrainingBatch, TrainingCourse, TrainingProgramme
from app.users.models import User
from app.intelligence.schemas import (
    IntelligenceInstitutionSummary,
    IntelligenceOverview,
    IntelligenceProgrammeDetail,
    IntelligenceTrainerSummary,
)

router = APIRouter(prefix="/intelligence", tags=["Intelligence & Analytics"])
ANALYSTS = require_roles("NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER")


@router.get("/overview", response_model=IntelligenceOverview)
def overview(db: Session = Depends(get_db), user: User = Depends(ANALYSTS)):
    trainees = db.scalar(select(func.count()).select_from(User).where(User.role == "TRAINEE")) or 0
    programmes = db.scalar(select(func.count()).select_from(TrainingProgramme)) or 0
    batches = db.scalar(select(func.count()).select_from(TrainingBatch)) or 0
    active_enrollments = db.scalar(select(func.count()).select_from(Enrollment).where(Enrollment.status == "ACTIVE")) or 0
    courses = db.scalar(select(func.count()).select_from(TrainingCourse)) or 0
    lessons = db.scalar(select(func.count()).select_from(CourseLesson)) or 0
    completed_lessons = db.scalar(select(func.count()).select_from(LessonProgress).where(LessonProgress.status == "COMPLETED")) or 0
    lesson_activity_rate = round((completed_lessons / lessons) * 100) if lessons else 0
    assessment_attempts = db.scalar(select(func.count()).select_from(AssessmentAttempt)) or 0
    assessment_passes = db.scalar(select(func.count()).select_from(AssessmentAttempt).where(AssessmentAttempt.result == "PASS")) or 0
    assessment_pass_rate = round((assessment_passes / assessment_attempts) * 100) if assessment_attempts else 0
    credentials_issued = db.scalar(select(func.count()).select_from(Credential)) or 0
    published_jobs = db.scalar(select(func.count()).select_from(JobPosting).where(JobPosting.status == "PUBLISHED")) or 0
    job_applications = db.scalar(select(func.count()).select_from(JobApplication)) or 0
    selected_applications = db.scalar(select(func.count()).select_from(JobApplication).where(JobApplication.status == "SELECTED")) or 0
    placement_conversion_rate = round((selected_applications / job_applications) * 100) if job_applications else 0
    statuses = {status: count for status, count in db.execute(select(JobApplication.status, func.count()).group_by(JobApplication.status)).all()}
    programme_rows = db.execute(
        select(TrainingProgramme.id, TrainingProgramme.code, TrainingProgramme.title, TrainingProgramme.status, func.count(TrainingBatch.id).label("batch_count"))
        .outerjoin(TrainingBatch, TrainingBatch.programme_id == TrainingProgramme.id)
        .group_by(TrainingProgramme.id, TrainingProgramme.code, TrainingProgramme.title, TrainingProgramme.status)
        .order_by(TrainingProgramme.created_at.desc()).limit(8)
    ).all()
    programme_summary = [{"id": r.id, "code": r.code, "title": r.title, "status": r.status, "batch_count": r.batch_count} for r in programme_rows]
    return IntelligenceOverview(
        trainees=trainees, programmes=programmes, batches=batches, active_enrollments=active_enrollments,
        courses=courses, lessons=lessons, completed_lesson_records=completed_lessons, lesson_activity_rate=lesson_activity_rate,
        assessment_attempts=assessment_attempts, assessment_passes=assessment_passes, assessment_pass_rate=assessment_pass_rate,
        credentials_issued=credentials_issued, published_jobs=published_jobs, job_applications=job_applications,
        selected_applications=selected_applications, placement_conversion_rate=placement_conversion_rate,
        application_statuses=statuses, programme_summary=programme_summary,
    )


@router.get("/institutions", response_model=list[IntelligenceInstitutionSummary])
def institutions(db: Session = Depends(get_db), user: User = Depends(ANALYSTS)):
    rows = db.execute(select(Institution).order_by(Institution.name.asc())).scalars().all()
    result = []
    for institution in rows:
        programme_ids = select(TrainingProgramme.id).where(TrainingProgramme.institution_id == institution.id)
        programme_count = db.scalar(select(func.count()).select_from(TrainingProgramme).where(TrainingProgramme.institution_id == institution.id)) or 0
        batch_count = db.scalar(select(func.count()).select_from(TrainingBatch).where(TrainingBatch.programme_id.in_(programme_ids))) or 0
        trainee_count = db.scalar(select(func.count(func.distinct(Enrollment.trainee_id))).select_from(Enrollment).join(TrainingBatch, Enrollment.batch_id == TrainingBatch.id).join(TrainingProgramme, TrainingBatch.programme_id == TrainingProgramme.id).where(TrainingProgramme.institution_id == institution.id)) or 0
        active_count = db.scalar(select(func.count()).select_from(Enrollment).join(TrainingBatch, Enrollment.batch_id == TrainingBatch.id).join(TrainingProgramme, TrainingBatch.programme_id == TrainingProgramme.id).where(TrainingProgramme.institution_id == institution.id, Enrollment.status == "ACTIVE")) or 0
        result.append(IntelligenceInstitutionSummary(id=institution.id, name=institution.name, institution_type=institution.institution_type, state=institution.state, district=institution.district, programme_count=programme_count, batch_count=batch_count, trainee_count=trainee_count, active_enrollment_count=active_count))
    return result


@router.get("/trainers", response_model=list[IntelligenceTrainerSummary])
def trainers(db: Session = Depends(get_db), user: User = Depends(ANALYSTS)):
    rows = db.execute(select(User).where(User.role == "TRAINER", User.is_active.is_(True)).order_by(User.full_name.asc())).scalars().all()
    result = []
    for trainer in rows:
        batch_count = db.scalar(select(func.count()).select_from(TrainingBatch).where(TrainingBatch.trainer_id == trainer.id)) or 0
        active_batch_count = db.scalar(select(func.count()).select_from(TrainingBatch).where(TrainingBatch.trainer_id == trainer.id, TrainingBatch.status == "ACTIVE")) or 0
        trainee_count = db.scalar(select(func.count(func.distinct(Enrollment.trainee_id))).select_from(Enrollment).join(TrainingBatch, Enrollment.batch_id == TrainingBatch.id).where(TrainingBatch.trainer_id == trainer.id)) or 0
        result.append(IntelligenceTrainerSummary(id=trainer.id, full_name=trainer.full_name, email=trainer.email, institution_id=trainer.institution_id, batch_count=batch_count, active_batch_count=active_batch_count, trainee_count=trainee_count))
    return result


@router.get("/programmes/{programme_id}", response_model=IntelligenceProgrammeDetail)
def programme_detail(programme_id: int, db: Session = Depends(get_db), user: User = Depends(ANALYSTS)):
    programme = db.get(TrainingProgramme, programme_id)
    if not programme:
        raise HTTPException(status_code=404, detail="Programme not found")
    institution = db.get(Institution, programme.institution_id)
    batches = db.execute(select(TrainingBatch).where(TrainingBatch.programme_id == programme_id).order_by(TrainingBatch.start_date.desc())).scalars().all()
    batch_ids = [b.id for b in batches]
    trainee_count = db.scalar(select(func.count(func.distinct(Enrollment.trainee_id))).where(Enrollment.batch_id.in_(batch_ids))) if batch_ids else 0
    active_enrollment_count = db.scalar(select(func.count()).select_from(Enrollment).where(Enrollment.batch_id.in_(batch_ids), Enrollment.status == "ACTIVE")) if batch_ids else 0
    course_ids = [r[0] for r in db.execute(select(TrainingCourse.id).where(TrainingCourse.programme_id == programme_id)).all()]
    completed_lesson_records = db.scalar(select(func.count()).select_from(LessonProgress).join(CourseLesson, LessonProgress.lesson_id == CourseLesson.id).join(CourseModule, CourseLesson.module_id == CourseModule.id).where(CourseModule.course_id.in_(course_ids), LessonProgress.status == "COMPLETED")) if course_ids else 0
    credential_count = db.scalar(select(func.count()).select_from(Credential).where(Credential.course_id.in_(course_ids))) if course_ids else 0
    batch_rows = []
    for b in batches:
        count = db.scalar(select(func.count()).select_from(Enrollment).where(Enrollment.batch_id == b.id)) or 0
        batch_rows.append({"id": b.id, "batch_code": b.batch_code, "start_date": b.start_date.isoformat(), "end_date": b.end_date.isoformat(), "venue": b.venue, "status": b.status, "capacity": b.capacity, "enrollment_count": count, "trainer_id": b.trainer_id})
    return IntelligenceProgrammeDetail(
        id=programme.id, code=programme.code, title=programme.title, description=programme.description,
        category=programme.category, mode=programme.mode, duration_days=programme.duration_days, capacity=programme.capacity,
        status=programme.status, institution_name=institution.name if institution else "Unknown",
        batch_count=len(batches), course_count=len(course_ids), trainee_count=trainee_count or 0,
        active_enrollment_count=active_enrollment_count or 0, completed_lesson_records=completed_lesson_records or 0,
        credential_count=credential_count or 0, batches=batch_rows,
    )

from app.attendance.models import AttendanceRecord, AttendanceSession
from app.intelligence.assistant_schemas import AssistantRequest, AssistantResponse
from app.careers.profile_models import CareerProfile
from app.training.models import CourseModule


def _assistant_response(answer: str, intent: str, sources: list[str], suggestions: list[str]) -> AssistantResponse:
    return AssistantResponse(answer=answer, intent=intent, sources=sources, suggestions=suggestions)


def _assistant_trainee(db: Session, user: User, message: str) -> AssistantResponse:
    text = message.lower()
    if any(k in text for k in ("job", "career", "employment", "vacanc", "opportunit")):
        jobs = db.scalars(select(JobPosting).where(JobPosting.status == "PUBLISHED").order_by(JobPosting.created_at.desc()).limit(5)).all()
        if not jobs:
            return _assistant_response("There are currently no published employment opportunities in the NCCT exchange.", "CAREER", ["Published job postings"], ["How is my learning progress?", "Show my credentials"])
        lines = [f"• {j.title} — {j.organization_name} ({j.location})" for j in jobs]
        return _assistant_response("Here are the latest published opportunities:\n" + "\n".join(lines), "CAREER", ["Published job postings"], ["How is my learning progress?", "Show my credentials"])

    if any(k in text for k in ("credential", "certificate", "certification")):
        rows = db.scalars(select(Credential).where(Credential.trainee_id == user.id).order_by(Credential.issued_at.desc())).all()
        if not rows:
            return _assistant_response("You do not have an issued NCCT credential yet.", "CREDENTIALS", ["Credential registry"], ["How is my learning progress?", "Show available jobs"])
        lines = [f"• {c.title} — {c.credential_number} ({c.status})" for c in rows]
        return _assistant_response("Your NCCT credentials:\n" + "\n".join(lines), "CREDENTIALS", ["Credential registry"], ["How is my learning progress?", "Show available jobs"])

    if any(k in text for k in ("attendance", "present", "absent", "late")):
        sessions = db.scalars(select(AttendanceSession).join(Enrollment, Enrollment.batch_id == AttendanceSession.batch_id).where(Enrollment.trainee_id == user.id, Enrollment.status == "ACTIVE").order_by(AttendanceSession.session_date.desc())).all()
        session_ids = [s.id for s in sessions]
        records = db.scalars(select(AttendanceRecord).where(AttendanceRecord.trainee_id == user.id, AttendanceRecord.session_id.in_(session_ids))).all() if session_ids else []
        by_session = {r.session_id: r.status for r in records}
        present = sum(1 for s in sessions if by_session.get(s.id) in ("PRESENT", "LATE"))
        absent = max(0, len(sessions) - len(records)) + sum(1 for r in records if r.status == "ABSENT")
        late = sum(1 for r in records if r.status == "LATE")
        rate = round(present / len(sessions) * 100, 1) if sessions else 0
        return _assistant_response(f"Your attendance rate is {rate}% across {len(sessions)} session(s). Present/on-time: {present - late}; Late: {late}; Absent: {absent}.", "ATTENDANCE", ["Attendance sessions and records"], ["How is my learning progress?", "Show my credentials"])

    if any(k in text for k in ("learning", "lesson", "course", "progress", "study", "module")):
        enrollments = db.scalars(select(Enrollment).where(Enrollment.trainee_id == user.id, Enrollment.status == "ACTIVE")).all()
        batch_ids = [e.batch_id for e in enrollments]
        programme_ids = [r[0] for r in db.execute(select(TrainingBatch.programme_id).where(TrainingBatch.id.in_(batch_ids))).all()] if batch_ids else []
        courses = db.scalars(select(TrainingCourse).where(TrainingCourse.programme_id.in_(programme_ids), TrainingCourse.status == "PUBLISHED").order_by(TrainingCourse.title.asc())).all() if programme_ids else []
        summaries = []
        for course in courses:
            lesson_ids = [r[0] for r in db.execute(select(CourseLesson.id).join(CourseModule, CourseLesson.module_id == CourseModule.id).where(CourseModule.course_id == course.id)).all()]
            completed = db.scalar(select(func.count()).select_from(LessonProgress).where(LessonProgress.trainee_id == user.id, LessonProgress.lesson_id.in_(lesson_ids), LessonProgress.status == "COMPLETED")) if lesson_ids else 0
            pct = round((completed or 0) / len(lesson_ids) * 100) if lesson_ids else 0
            summaries.append(f"• {course.title}: {pct}% ({completed or 0}/{len(lesson_ids)} lessons)")
        answer = "Your current learning progress:\n" + "\n".join(summaries) if summaries else "You do not have an active published course to report yet."
        return _assistant_response(answer, "LEARNING", ["Active enrollments", "Course and lesson progress"], ["What is my attendance?", "Show my credentials", "Show available jobs"])

    profile = db.scalar(select(CareerProfile).where(CareerProfile.trainee_id == user.id))
    profile_hint = f"Your profile lists skills: {profile.skills}." if profile and profile.skills else "Your career profile does not yet list skills."
    return _assistant_response(f"I can help with your NCCT learning, attendance, credentials and employment information. {profile_hint}", "GENERAL", ["NCCT trainee profile"], ["How is my learning progress?", "What is my attendance?", "Show my credentials", "Show available jobs"])


def _assistant_analyst(db: Session, user: User, message: str) -> AssistantResponse:
    text = message.lower()
    trainee_query = select(User).where(User.role == "TRAINEE", User.is_active.is_(True))
    if user.role == "INSTITUTE_ADMIN":
        trainee_query = trainee_query.join(Enrollment, Enrollment.trainee_id == User.id).join(TrainingBatch, TrainingBatch.id == Enrollment.batch_id).join(TrainingProgramme, TrainingProgramme.id == TrainingBatch.programme_id).where(TrainingProgramme.institution_id == user.institution_id)
    elif user.role == "TRAINER":
        trainee_query = trainee_query.join(Enrollment, Enrollment.trainee_id == User.id).join(TrainingBatch, TrainingBatch.id == Enrollment.batch_id).where(TrainingBatch.trainer_id == user.id)
    trainees = db.scalars(trainee_query.distinct()).all()
    trainee_ids = [t.id for t in trainees]
    if any(k in text for k in ("attendance", "low attendance", "absent")):
        rows = []
        for trainee in trainees:
            sessions = db.scalars(select(AttendanceSession).join(Enrollment, Enrollment.batch_id == AttendanceSession.batch_id).where(Enrollment.trainee_id == trainee.id, Enrollment.status == "ACTIVE")).all()
            if not sessions:
                continue
            ids = [s.id for s in sessions]
            records = db.scalars(select(AttendanceRecord).where(AttendanceRecord.trainee_id == trainee.id, AttendanceRecord.session_id.in_(ids))).all()
            attended = sum(1 for r in records if r.status in ("PRESENT", "LATE"))
            rate = round(attended / len(sessions) * 100, 1)
            if rate < 75:
                rows.append(f"• {trainee.full_name}: {rate}% ({attended}/{len(sessions)})")
        answer = "Trainees below the 75% attendance threshold:\n" + "\n".join(rows) if rows else "No trainees are currently below the 75% attendance threshold."
        return _assistant_response(answer, "ATTENDANCE_ALERTS", ["Attendance sessions, records and active enrollments"], ["Summarize training activity", "Show employment pipeline"])
    if any(k in text for k in ("employment", "job", "application", "placement")):
        jobs = db.scalar(select(func.count()).select_from(JobPosting).where(JobPosting.status == "PUBLISHED")) or 0
        application_query = select(func.count()).select_from(JobApplication)
        if user.role != "NCCT_ADMIN":
            application_query = application_query.where(JobApplication.trainee_id.in_(trainee_ids))
        applications = db.scalar(application_query) or 0
        selected_query = select(func.count()).select_from(JobApplication).where(JobApplication.status == "SELECTED")
        if user.role != "NCCT_ADMIN":
            selected_query = selected_query.where(JobApplication.trainee_id.in_(trainee_ids))
        selected = db.scalar(selected_query) or 0
        return _assistant_response(f"The employment exchange currently has {jobs} published job(s), {applications} application(s), and {selected} selected application(s) in your permitted trainee scope.", "EMPLOYMENT", ["Published jobs and applications"], ["Show low-attendance trainees", "Summarize training activity"])
    trainees_count = len(trainees)
    active_query = select(func.count()).select_from(Enrollment).where(Enrollment.status == "ACTIVE")
    completed_query = select(func.count()).select_from(LessonProgress).where(LessonProgress.status == "COMPLETED")
    if user.role != "NCCT_ADMIN":
        active_query = active_query.where(Enrollment.trainee_id.in_(trainee_ids))
        completed_query = completed_query.where(LessonProgress.trainee_id.in_(trainee_ids))
    active = db.scalar(active_query) or 0
    completed = db.scalar(completed_query) or 0
    return _assistant_response(f"Current operational snapshot in your permitted scope: {trainees_count} trainees, {active} active enrollments, and {completed} completed lesson records.", "OVERVIEW", ["Training ERP and LMS operational counts"], ["Show low-attendance trainees", "Show employment pipeline"])


@router.post("/assistant", response_model=AssistantResponse)
def assistant(payload: AssistantRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("TRAINEE", "NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER"))):
    if user.role == "TRAINEE":
        return _assistant_trainee(db, user, payload.message.strip())
    return _assistant_analyst(db, user, payload.message.strip())
