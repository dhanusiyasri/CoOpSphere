from datetime import date
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.training.models import CourseModule, Enrollment, TrainingBatch, TrainingCourse, TrainingProgramme
from app.training.schedule_models import TrainingSchedule
from app.training.schedule_schemas import ScheduleAttendanceResponse, ScheduleCreate, ScheduleResponse
from app.attendance.models import AttendanceSession
from app.users.models import User

router = APIRouter(prefix="/training/schedules", tags=["Training Schedule"])
MANAGERS = require_roles("NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER")


def _scope_manager(query, current_user: User):
    if current_user.role == "TRAINER":
        query = query.where(TrainingBatch.trainer_id == current_user.id)
    elif current_user.role == "INSTITUTE_ADMIN":
        query = query.join(TrainingProgramme, TrainingProgramme.id == TrainingBatch.programme_id).where(
            TrainingProgramme.institution_id == current_user.institution_id
        )
    return query


def _row(db: Session, schedule: TrainingSchedule) -> ScheduleResponse:
    batch = db.get(TrainingBatch, schedule.batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found for schedule")
    programme = db.get(TrainingProgramme, batch.programme_id)
    course = db.get(TrainingCourse, schedule.course_id) if schedule.course_id else None
    module = db.get(CourseModule, schedule.module_id) if schedule.module_id else None
    trainer = db.get(User, schedule.trainer_id) if schedule.trainer_id else None
    return ScheduleResponse(
        **{k: getattr(schedule, k) for k in (
            "batch_id", "course_id", "module_id", "trainer_id", "session_date", "start_time", "end_time",
            "topic", "venue", "mode", "status", "notes", "id", "attendance_session_id", "created_by_id", "created_at"
        )},
        batch_code=batch.batch_code,
        programme_title=programme.title if programme else "Unknown programme",
        course_title=course.title if course else None,
        module_title=module.title if module else None,
        trainer_name=trainer.full_name if trainer else None,
    )


@router.get("", response_model=list[ScheduleResponse])
def list_schedules(
    batch_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(TrainingSchedule, TrainingBatch).join(TrainingBatch, TrainingBatch.id == TrainingSchedule.batch_id)
    if current_user.role == "TRAINEE":
        query = query.join(
            Enrollment,
            (Enrollment.batch_id == TrainingBatch.id) & (Enrollment.trainee_id == current_user.id),
        ).where(Enrollment.status == "ACTIVE")
    elif current_user.role in {"NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER"}:
        query = _scope_manager(query, current_user)
    else:
        raise HTTPException(status_code=403, detail="You do not have access to training schedules")
    if batch_id:
        query = query.where(TrainingSchedule.batch_id == batch_id)
    if from_date:
        query = query.where(TrainingSchedule.session_date >= from_date)
    if to_date:
        query = query.where(TrainingSchedule.session_date <= to_date)
    rows = db.execute(
        query.order_by(TrainingSchedule.session_date.asc(), TrainingSchedule.start_time.asc(), TrainingSchedule.id.asc())
    ).all()
    return [_row(db, schedule) for schedule, _batch in rows]


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(MANAGERS),
):
    batch = db.get(TrainingBatch, payload.batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if current_user.role == "INSTITUTE_ADMIN":
        programme = db.get(TrainingProgramme, batch.programme_id)
        if not programme or programme.institution_id != current_user.institution_id:
            raise HTTPException(status_code=403, detail="You can only schedule sessions for your institution")
    if current_user.role == "TRAINER" and batch.trainer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only schedule sessions for your assigned batches")
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    if payload.session_date < batch.start_date or payload.session_date > batch.end_date:
        raise HTTPException(status_code=400, detail="Session date must fall within the batch dates")
    if db.scalar(select(TrainingSchedule).where(
        TrainingSchedule.batch_id == payload.batch_id,
        TrainingSchedule.session_date == payload.session_date,
        TrainingSchedule.start_time == payload.start_time,
    )):
        raise HTTPException(status_code=409, detail="A schedule already exists for this batch and start time")

    course = db.get(TrainingCourse, payload.course_id) if payload.course_id else None
    if payload.course_id and (not course or course.programme_id != batch.programme_id):
        raise HTTPException(status_code=400, detail="Selected course does not belong to this batch programme")
    module = db.get(CourseModule, payload.module_id) if payload.module_id else None
    if payload.module_id and (not module or not course or module.course_id != course.id):
        raise HTTPException(status_code=400, detail="Selected module does not belong to the selected course")

    trainer_id = payload.trainer_id if payload.trainer_id is not None else batch.trainer_id
    if trainer_id:
        trainer = db.get(User, trainer_id)
        if not trainer or not trainer.is_active or trainer.role != "TRAINER":
            raise HTTPException(status_code=400, detail="Selected trainer is not an active trainer")
        if current_user.role == "TRAINER" and trainer_id != current_user.id:
            raise HTTPException(status_code=403, detail="A trainer can only schedule themselves")

    schedule = TrainingSchedule(**payload.model_dump(exclude_none=True), trainer_id=trainer_id, created_by_id=current_user.id)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return _row(db, schedule)


@router.post("/{schedule_id}/attendance", response_model=ScheduleAttendanceResponse)
def create_attendance_for_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(MANAGERS),
):
    schedule = db.get(TrainingSchedule, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    batch = db.get(TrainingBatch, schedule.batch_id)
    if current_user.role == "INSTITUTE_ADMIN":
        programme = db.get(TrainingProgramme, batch.programme_id) if batch else None
        if not programme or programme.institution_id != current_user.institution_id:
            raise HTTPException(status_code=403, detail="You can only manage your institution's schedules")
    if current_user.role == "TRAINER" and (not batch or batch.trainer_id != current_user.id):
        raise HTTPException(status_code=403, detail="You can only open attendance for your assigned batches")
    if schedule.attendance_session_id:
        session = db.get(AttendanceSession, schedule.attendance_session_id)
        if session:
            return ScheduleAttendanceResponse(schedule_id=schedule.id, attendance_session_id=session.id, access_code=session.access_code)

    existing = db.scalar(select(AttendanceSession).where(
        AttendanceSession.batch_id == schedule.batch_id,
        AttendanceSession.session_date == schedule.session_date,
        AttendanceSession.start_time == schedule.start_time,
    ))
    if existing:
        schedule.attendance_session_id = existing.id
        db.commit()
        return ScheduleAttendanceResponse(schedule_id=schedule.id, attendance_session_id=existing.id, access_code=existing.access_code)

    for _ in range(20):
        access_code = secrets.token_hex(4).upper()
        if not db.scalar(select(AttendanceSession).where(AttendanceSession.access_code == access_code)):
            break
    else:
        raise HTTPException(status_code=500, detail="Could not generate attendance access code")

    session = AttendanceSession(
        batch_id=schedule.batch_id,
        session_date=schedule.session_date,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        topic=schedule.topic,
        notes=schedule.notes,
        status="SCHEDULED",
        access_code=access_code,
        created_by_id=current_user.id,
    )
    db.add(session)
    db.flush()
    schedule.attendance_session_id = session.id
    db.commit()
    return ScheduleAttendanceResponse(schedule_id=schedule.id, attendance_session_id=session.id, access_code=session.access_code)
