from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.training.models import TrainingBatch, TrainingProgramme, Enrollment
from app.training.logistics_models import TrainingLogisticsPlan, TrainingAccommodationAllocation
from app.training.logistics_schemas import LogisticsPlanCreate, LogisticsPlanResponse, AccommodationCreate, AccommodationResponse, EligibleTraineeResponse
from app.users.models import User

router = APIRouter(prefix="/training/logistics", tags=["Training Logistics"])
MANAGERS = require_roles("NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER")

def _check_batch_scope(db: Session, batch: TrainingBatch, user: User):
    programme = db.get(TrainingProgramme, batch.programme_id)
    if not programme:
        raise HTTPException(status_code=404, detail="Programme not found")
    if user.role == "INSTITUTE_ADMIN" and programme.institution_id != user.institution_id:
        raise HTTPException(status_code=403, detail="You can only manage logistics for your institution")
    if user.role == "TRAINER" and batch.trainer_id != user.id:
        raise HTTPException(status_code=403, detail="You can only manage logistics for your assigned batches")
    return programme

def _plan_response(db: Session, plan: TrainingLogisticsPlan):
    batch = db.get(TrainingBatch, plan.batch_id)
    programme = db.get(TrainingProgramme, batch.programme_id) if batch else None
    allocated = db.scalar(select(func.count(TrainingAccommodationAllocation.id)).where(
        TrainingAccommodationAllocation.batch_id == plan.batch_id,
        TrainingAccommodationAllocation.status == "ALLOCATED",
    )) or 0
    return LogisticsPlanResponse(
        **{k:getattr(plan,k) for k in (
            "batch_id","hostel_required","hostel_name","rooms_available","meals_included","meal_notes",
            "transport_required","pickup_point","transport_notes","coordinator_name","coordinator_phone",
            "notes","id","created_by_id","created_at"
        )},
        batch_code=batch.batch_code if batch else "Unknown",
        programme_title=programme.title if programme else "Unknown",
        allocated_count=int(allocated),
    )

@router.get("/plans", response_model=list[LogisticsPlanResponse])
def list_plans(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {"NCCT_ADMIN","INSTITUTE_ADMIN","TRAINER","TRAINEE"}:
        raise HTTPException(status_code=403, detail="You do not have access to training logistics")
    q = select(TrainingLogisticsPlan, TrainingBatch).join(TrainingBatch, TrainingBatch.id == TrainingLogisticsPlan.batch_id)
    if user.role == "TRAINEE":
        q = q.join(Enrollment, Enrollment.batch_id == TrainingBatch.id).where(
            Enrollment.trainee_id == user.id, Enrollment.status == "ACTIVE"
        )
    elif user.role == "INSTITUTE_ADMIN":
        q = q.join(TrainingProgramme, TrainingProgramme.id == TrainingBatch.programme_id).where(
            TrainingProgramme.institution_id == user.institution_id
        )
    elif user.role == "TRAINER":
        q = q.where(TrainingBatch.trainer_id == user.id)
    rows = db.execute(q.order_by(TrainingBatch.start_date.desc())).all()
    return [_plan_response(db, p) for p,_ in rows]

@router.post("/plans", response_model=LogisticsPlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(payload: LogisticsPlanCreate, db: Session = Depends(get_db), user: User = Depends(MANAGERS)):
    batch = db.get(TrainingBatch, payload.batch_id)
    if not batch: raise HTTPException(status_code=404, detail="Batch not found")
    _check_batch_scope(db, batch, user)
    existing = db.scalar(select(TrainingLogisticsPlan).where(TrainingLogisticsPlan.batch_id == batch.id))
    if existing:
        for k,v in payload.model_dump().items():
            if k != "batch_id": setattr(existing,k,v)
        db.commit(); db.refresh(existing)
        return _plan_response(db, existing)
    if payload.rooms_available < 0: raise HTTPException(status_code=400, detail="Rooms available cannot be negative")
    plan = TrainingLogisticsPlan(**payload.model_dump(), created_by_id=user.id)
    db.add(plan); db.commit(); db.refresh(plan)
    return _plan_response(db, plan)

@router.get("/allocations", response_model=list[AccommodationResponse])
def list_allocations(batch_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {"NCCT_ADMIN","INSTITUTE_ADMIN","TRAINER","TRAINEE"}:
        raise HTTPException(status_code=403, detail="You do not have access to accommodation allocations")
    q = select(TrainingAccommodationAllocation, User).join(User, User.id == TrainingAccommodationAllocation.trainee_id)
    if user.role == "TRAINEE":
        q = q.where(TrainingAccommodationAllocation.trainee_id == user.id)
    elif user.role == "TRAINER":
        q = q.join(TrainingBatch, TrainingBatch.id == TrainingAccommodationAllocation.batch_id).where(TrainingBatch.trainer_id == user.id)
    elif user.role == "INSTITUTE_ADMIN":
        q = q.join(TrainingBatch, TrainingBatch.id == TrainingAccommodationAllocation.batch_id).join(
            TrainingProgramme, TrainingProgramme.id == TrainingBatch.programme_id
        ).where(TrainingProgramme.institution_id == user.institution_id)
    if batch_id: q = q.where(TrainingAccommodationAllocation.batch_id == batch_id)
    rows = db.execute(q.order_by(TrainingAccommodationAllocation.room_number, TrainingAccommodationAllocation.bed_number)).all()
    return [AccommodationResponse(
        **{k:getattr(a,k) for k in ("batch_id","trainee_id","room_number","bed_number","status","notes","id","allocated_by_id","allocated_at")},
        trainee_name=u.full_name, trainee_email=u.email
    ) for a,u in rows]

@router.get("/eligible-trainees", response_model=list[EligibleTraineeResponse])
def list_eligible_trainees(batch_id: int, db: Session = Depends(get_db), user: User = Depends(MANAGERS)):
    # Use the same manager dependency as accommodation-plan/allocation writes so the
    # eligibility lookup cannot drift from the authorization rules used by this page.
    batch = db.get(TrainingBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    _check_batch_scope(db, batch, user)
    rows = db.execute(
        select(Enrollment, User)
        .join(User, User.id == Enrollment.trainee_id)
        .where(
            Enrollment.batch_id == batch_id,
            Enrollment.status == "ACTIVE",
            User.role == "TRAINEE",
            User.is_active.is_(True),
        )
        .order_by(User.full_name.asc())
    ).all()
    return [
        EligibleTraineeResponse(
            trainee_id=enrollment.trainee_id,
            full_name=trainee.full_name,
            email=trainee.email,
            enrollment_id=enrollment.id,
            enrollment_status=enrollment.status,
        )
        for enrollment, trainee in rows
    ]


@router.post("/allocations", response_model=AccommodationResponse, status_code=status.HTTP_201_CREATED)
def create_allocation(payload: AccommodationCreate, db: Session = Depends(get_db), user: User = Depends(MANAGERS)):
    batch = db.get(TrainingBatch, payload.batch_id)
    if not batch: raise HTTPException(status_code=404, detail="Batch not found")
    _check_batch_scope(db, batch, user)
    trainee = db.get(User, payload.trainee_id)
    if not trainee or not trainee.is_active or trainee.role != "TRAINEE":
        raise HTTPException(status_code=400, detail="Selected user is not an active trainee")
    enrolled = db.scalar(select(Enrollment).where(
        Enrollment.batch_id == batch.id, Enrollment.trainee_id == trainee.id, Enrollment.status == "ACTIVE"
    ))
    if not enrolled: raise HTTPException(status_code=400, detail="Trainee must have an active enrollment in this batch")
    plan = db.scalar(select(TrainingLogisticsPlan).where(TrainingLogisticsPlan.batch_id == batch.id))
    if not plan or not plan.hostel_required: raise HTTPException(status_code=400, detail="Hostel accommodation is not enabled for this batch")
    existing = db.scalar(select(TrainingAccommodationAllocation).where(
        TrainingAccommodationAllocation.batch_id == batch.id, TrainingAccommodationAllocation.trainee_id == trainee.id
    ))
    if existing:
        for k,v in payload.model_dump().items():
            if k not in {"batch_id","trainee_id"}: setattr(existing,k,v)
        db.commit(); db.refresh(existing)
        return AccommodationResponse(**{k:getattr(existing,k) for k in ("batch_id","trainee_id","room_number","bed_number","status","notes","id","allocated_by_id","allocated_at")}, trainee_name=trainee.full_name, trainee_email=trainee.email)
    if plan.rooms_available and (db.scalar(select(func.count(TrainingAccommodationAllocation.id)).where(
        TrainingAccommodationAllocation.batch_id == batch.id, TrainingAccommodationAllocation.status == "ALLOCATED"
    )) or 0) >= plan.rooms_available:
        raise HTTPException(status_code=409, detail="Configured accommodation capacity is full")
    allocation = TrainingAccommodationAllocation(**payload.model_dump(), allocated_by_id=user.id)
    db.add(allocation); db.commit(); db.refresh(allocation)
    return AccommodationResponse(**{k:getattr(allocation,k) for k in ("batch_id","trainee_id","room_number","bed_number","status","notes","id","allocated_by_id","allocated_at")}, trainee_name=trainee.full_name, trainee_email=trainee.email)
