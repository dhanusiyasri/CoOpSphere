from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.training.models import Enrollment, Nomination, TrainingBatch, TrainingProgramme
from app.users.models import User


def get_programme_or_404(db: Session, programme_id: int) -> TrainingProgramme:
    programme = db.get(TrainingProgramme, programme_id)
    if not programme:
        raise HTTPException(status_code=404, detail="Training programme not found")
    return programme


def get_batch_or_404(db: Session, batch_id: int) -> TrainingBatch:
    batch = db.get(TrainingBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Training batch not found")
    return batch


def get_trainee_or_404(db: Session, trainee_id: int) -> User:
    trainee = db.get(User, trainee_id)
    if not trainee or not trainee.is_active:
        raise HTTPException(status_code=404, detail="Trainee not found")
    return trainee


def create_nomination(db: Session, batch_id: int, trainee_id: int, nominated_by_id: int, remarks: str | None):
    batch = get_batch_or_404(db, batch_id)
    trainee = get_trainee_or_404(db, trainee_id)

    if trainee.role != "TRAINEE":
        raise HTTPException(status_code=400, detail="Only users with the TRAINEE role can be nominated")
    if batch.status not in {"OPEN", "PLANNED"}:
        raise HTTPException(status_code=409, detail="This batch is not accepting nominations")

    programme = get_programme_or_404(db, batch.programme_id)
    if programme.status not in {"PUBLISHED", "ACTIVE"}:
        raise HTTPException(status_code=409, detail="The programme is not open for nominations")

    existing = db.scalar(select(Nomination).where(Nomination.batch_id == batch_id, Nomination.trainee_id == trainee_id))
    if existing:
        if existing.status == "REJECTED":
            existing.status = "SUBMITTED"
            existing.remarks = remarks
            existing.nominated_by_id = nominated_by_id
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(status_code=409, detail="Trainee is already nominated for this batch")

    enrolled_count = db.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.batch_id == batch.id,
            Enrollment.status.in_(["ACTIVE", "COMPLETED"]),
        )
    ) or 0
    pending_count = db.scalar(
        select(func.count(Nomination.id)).where(
            Nomination.batch_id == batch.id,
            Nomination.status == "SUBMITTED",
        )
    ) or 0
    if enrolled_count + pending_count >= batch.capacity:
        raise HTTPException(status_code=409, detail="No nomination capacity remains for this batch")

    nomination = Nomination(batch_id=batch_id, trainee_id=trainee_id, nominated_by_id=nominated_by_id, remarks=remarks)
    db.add(nomination)
    db.commit()
    db.refresh(nomination)
    return nomination


def reject_nomination(db: Session, nomination_id: int, remarks: str | None = None):
    nomination = db.get(Nomination, nomination_id)
    if not nomination:
        raise HTTPException(status_code=404, detail="Nomination not found")
    if nomination.status == "APPROVED":
        raise HTTPException(status_code=409, detail="Approved nominations cannot be rejected")
    nomination.status = "REJECTED"
    if remarks:
        nomination.remarks = remarks
    db.commit()
    db.refresh(nomination)
    return nomination


def approve_nomination(db: Session, nomination_id: int):
    nomination = db.get(Nomination, nomination_id)
    if not nomination:
        raise HTTPException(status_code=404, detail="Nomination not found")
    if nomination.status == "REJECTED":
        raise HTTPException(status_code=409, detail="Rejected nominations cannot be enrolled")
    existing = db.scalar(select(Enrollment).where(Enrollment.batch_id == nomination.batch_id, Enrollment.trainee_id == nomination.trainee_id))
    if existing:
        nomination.status = "APPROVED"
        db.commit()
        return existing

    batch = get_batch_or_404(db, nomination.batch_id)
    enrolled_count = db.scalar(select(func.count(Enrollment.id)).where(Enrollment.batch_id == batch.id, Enrollment.status.in_(["ACTIVE", "COMPLETED"]))) or 0
    if enrolled_count >= batch.capacity:
        raise HTTPException(status_code=409, detail="Batch capacity is full")

    nomination.status = "APPROVED"
    enrollment = Enrollment(batch_id=batch.id, trainee_id=nomination.trainee_id, nomination_id=nomination.id, status="ACTIVE")
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment
