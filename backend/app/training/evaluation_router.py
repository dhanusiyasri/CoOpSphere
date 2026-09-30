from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.training.models import TrainingBatch, Enrollment
from app.training.schedule_models import TrainingSchedule
from app.training.evaluation_models import TrainingSessionFeedback
from app.training.evaluation_schemas import FeedbackCreate, FeedbackResponse, FeedbackSummary
from app.users.models import User

router = APIRouter(prefix="/training/evaluations", tags=["Training Evaluation"])
MANAGERS = require_roles("NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER")

def _scope_batch(db, batch, user):
    if user.role == "TRAINER" and batch.trainer_id != user.id:
        raise HTTPException(403, "You can only manage feedback for your assigned batches")
    if user.role == "INSTITUTE_ADMIN":
        from app.training.models import TrainingProgramme
        programme = db.get(TrainingProgramme, batch.programme_id)
        if not programme or programme.institution_id != user.institution_id:
            raise HTTPException(403, "You can only manage feedback for your institution")

def _response(row, trainee):
    return FeedbackResponse(
        id=row.id, schedule_id=row.schedule_id, batch_id=row.batch_id, trainee_id=row.trainee_id,
        trainee_name=trainee.full_name, submitted_at=row.submitted_at,
        content_rating=row.content_rating, trainer_rating=row.trainer_rating,
        venue_rating=row.venue_rating, overall_rating=row.overall_rating, comments=row.comments,
    )

@router.get("", response_model=list[FeedbackResponse])
def list_feedback(batch_id: int | None = None, schedule_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(TrainingSessionFeedback, User).join(User, User.id == TrainingSessionFeedback.trainee_id)
    if user.role == "TRAINEE":
        q = q.where(TrainingSessionFeedback.trainee_id == user.id)
    elif user.role == "TRAINER":
        q = q.join(TrainingBatch, TrainingBatch.id == TrainingSessionFeedback.batch_id).where(TrainingBatch.trainer_id == user.id)
    elif user.role == "INSTITUTE_ADMIN":
        from app.training.models import TrainingProgramme
        q = q.join(TrainingBatch, TrainingBatch.id == TrainingSessionFeedback.batch_id).join(TrainingProgramme, TrainingProgramme.id == TrainingBatch.programme_id).where(TrainingProgramme.institution_id == user.institution_id)
    elif user.role != "NCCT_ADMIN":
        raise HTTPException(403, "You do not have access to training evaluations")
    if batch_id: q = q.where(TrainingSessionFeedback.batch_id == batch_id)
    if schedule_id: q = q.where(TrainingSessionFeedback.schedule_id == schedule_id)
    rows = db.execute(q.order_by(TrainingSessionFeedback.submitted_at.desc())).all()
    return [_response(r,u) for r,u in rows]

@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(payload: FeedbackCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("TRAINEE"))):
    schedule = db.get(TrainingSchedule, payload.schedule_id)
    if not schedule: raise HTTPException(404, "Training session not found")
    enrolled = db.scalar(select(Enrollment).where(Enrollment.batch_id == schedule.batch_id, Enrollment.trainee_id == user.id, Enrollment.status == "ACTIVE"))
    if not enrolled: raise HTTPException(403, "You are not actively enrolled in this training batch")
    existing = db.scalar(select(TrainingSessionFeedback).where(TrainingSessionFeedback.schedule_id == schedule.id, TrainingSessionFeedback.trainee_id == user.id))
    if existing: raise HTTPException(409, "You have already submitted feedback for this session")
    row = TrainingSessionFeedback(**payload.model_dump(), batch_id=schedule.batch_id, trainee_id=user.id)
    db.add(row); db.commit(); db.refresh(row)
    return _response(row, user)

@router.get("/summary", response_model=list[FeedbackSummary])
def feedback_summary(batch_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(MANAGERS)):
    q = select(
        TrainingSessionFeedback.schedule_id, TrainingSchedule.topic, TrainingSchedule.session_date, TrainingBatch.batch_code,
        func.count(TrainingSessionFeedback.id),
        func.avg(TrainingSessionFeedback.content_rating), func.avg(TrainingSessionFeedback.trainer_rating),
        func.avg(TrainingSessionFeedback.venue_rating), func.avg(TrainingSessionFeedback.overall_rating),
    ).join(TrainingSchedule, TrainingSchedule.id == TrainingSessionFeedback.schedule_id).join(TrainingBatch, TrainingBatch.id == TrainingSessionFeedback.batch_id)
    if user.role == "TRAINER": q = q.where(TrainingBatch.trainer_id == user.id)
    elif user.role == "INSTITUTE_ADMIN":
        from app.training.models import TrainingProgramme
        q = q.join(TrainingProgramme, TrainingProgramme.id == TrainingBatch.programme_id).where(TrainingProgramme.institution_id == user.institution_id)
    if batch_id: q = q.where(TrainingSessionFeedback.batch_id == batch_id)
    q = q.group_by(TrainingSessionFeedback.schedule_id, TrainingSchedule.topic, TrainingSchedule.session_date, TrainingBatch.batch_code).order_by(TrainingSchedule.session_date.desc())
    rows = db.execute(q).all()
    return [FeedbackSummary(schedule_id=r[0], topic=r[1], session_date=r[2].isoformat(), batch_code=r[3], responses=int(r[4]), average_content=round(float(r[5]),2), average_trainer=round(float(r[6]),2), average_venue=round(float(r[7]),2), average_overall=round(float(r[8]),2)) for r in rows]
