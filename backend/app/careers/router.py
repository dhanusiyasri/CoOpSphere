from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.careers.models import EmploymentOutcome, JobApplication, JobPosting, EmploymentFollowUp
from app.careers.schemas import (
    ApplicationStatusUpdate,
    JobApplicationCreate,
    JobApplicationResponse,
    JobPostingCreate,
    JobPostingResponse,
    InterviewScheduleRequest, InterviewCancelRequest, OfferCreateRequest, OfferResponseRequest,
    PlacementUpdateRequest, PlacementResponse, PlacementSummary, PlacementAnalytics,
    EmploymentFollowUpRequest, EmploymentFollowUpResponse,
)
from app.users.models import User

router = APIRouter(prefix="/careers", tags=["Careers & Employment"])
TRAINEES = require_roles("TRAINEE")
EMPLOYERS = require_roles("EMPLOYER", "NCCT_ADMIN")


def _application_response(application: JobApplication, job: JobPosting) -> JobApplicationResponse:
    return JobApplicationResponse(
        id=application.id, job_id=job.id, trainee_id=application.trainee_id,
        job_title=job.title, organization_name=job.organization_name,
        status=application.status, cover_note=application.cover_note,
        applied_at=application.applied_at, updated_at=application.updated_at,
        interview_scheduled_at=application.interview_scheduled_at,
        interview_mode=application.interview_mode,
        interview_location_or_link=application.interview_location_or_link,
        interview_notes=application.interview_notes,
        offer_status=application.offer_status,
        offer_offered_at=application.offer_offered_at,
        offer_expires_at=application.offer_expires_at,
        offer_salary=application.offer_salary,
        offer_employment_type=application.offer_employment_type,
        offer_notes=application.offer_notes,
        offer_responded_at=application.offer_responded_at,
    )


def _placement_response(outcome: EmploymentOutcome, application: JobApplication, job: JobPosting) -> PlacementResponse:
    return PlacementResponse(
        id=outcome.id, application_id=application.id, trainee_id=outcome.trainee_id,
        employer_id=outcome.employer_id, job_id=job.id, job_title=job.title,
        organization_name=job.organization_name, status=outcome.status,
        joining_date=outcome.joining_date, notes=outcome.notes, updated_at=outcome.updated_at,
    )


def _followup_response(row: EmploymentFollowUp) -> EmploymentFollowUpResponse:
    return EmploymentFollowUpResponse(
        id=row.id, placement_id=row.placement_id, trainee_id=row.trainee_id, employer_id=row.employer_id,
        checkpoint=row.checkpoint, status=row.status, notes=row.notes,
        employer_feedback=row.employer_feedback, trainee_feedback=row.trainee_feedback,
        checked_at=row.checked_at, updated_at=row.updated_at,
    )

@router.get("/jobs", response_model=list[JobPostingResponse])
def list_jobs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(JobPosting).order_by(JobPosting.created_at.desc())
    if user.role == "TRAINEE":
        query = query.where(JobPosting.status == "PUBLISHED")
    elif user.role == "EMPLOYER":
        query = query.where(JobPosting.employer_id == user.id)
    return db.scalars(query).all()


@router.post("/jobs", response_model=JobPostingResponse)
def create_job(payload: JobPostingCreate, db: Session = Depends(get_db), user: User = Depends(EMPLOYERS)):
    status = payload.status if user.role == "NCCT_ADMIN" else "PUBLISHED"
    job = JobPosting(employer_id=user.id, status=status, **payload.model_dump(exclude={"status"}))
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/jobs/{job_id}", response_model=JobPostingResponse)
def get_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = db.get(JobPosting, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if user.role == "TRAINEE" and job.status != "PUBLISHED":
        raise HTTPException(status_code=404, detail="Job not found")
    if user.role == "EMPLOYER" and job.employer_id != user.id:
        raise HTTPException(status_code=403, detail="You cannot view this employer posting")
    return job


@router.post("/jobs/{job_id}/apply", response_model=JobApplicationResponse)
def apply_job(job_id: int, payload: JobApplicationCreate, db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    job = db.get(JobPosting, job_id)
    if not job or job.status != "PUBLISHED":
        raise HTTPException(status_code=404, detail="Published job not found")
    if job.closing_date and job.closing_date < date.today():
        raise HTTPException(status_code=400, detail="This job application window is closed")
    existing = db.scalar(select(JobApplication).where(JobApplication.job_id == job_id, JobApplication.trainee_id == user.id))
    if existing:
        raise HTTPException(status_code=409, detail="You have already applied to this job")
    application = JobApplication(job_id=job_id, trainee_id=user.id, cover_note=payload.cover_note)
    db.add(application)
    db.commit()
    db.refresh(application)
    return _application_response(application, job)


@router.get("/my-applications", response_model=list[JobApplicationResponse])
def my_applications(db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    rows = db.execute(
        select(JobApplication, JobPosting)
        .join(JobPosting, JobPosting.id == JobApplication.job_id)
        .where(JobApplication.trainee_id == user.id)
        .order_by(JobApplication.applied_at.desc())
    ).all()
    return [
        _application_response(app, job)
        for app, job in rows
    ]


@router.get("/employer-applications", response_model=list[JobApplicationResponse])
def employer_applications(db: Session = Depends(get_db), user: User = Depends(EMPLOYERS)):
    rows = db.execute(
        select(JobApplication, JobPosting)
        .join(JobPosting, JobPosting.id == JobApplication.job_id)
        .where(JobPosting.employer_id == user.id)
        .order_by(JobApplication.applied_at.desc())
    ).all()
    return [
        _application_response(app, job)
        for app, job in rows
    ]


@router.post("/applications/{application_id}/status", response_model=JobApplicationResponse)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(EMPLOYERS),
):
    application = db.get(JobApplication, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    job = db.get(JobPosting, application.job_id)
    if not job or (user.role != "NCCT_ADMIN" and job.employer_id != user.id):
        raise HTTPException(status_code=403, detail="You cannot update this application")
    # Keep the hiring workflow ordered: shortlist, interview, then select.
    requested_status = payload.status.upper().strip()
    transitions = {
        "APPLIED": {"SHORTLISTED", "REJECTED"},
        "SHORTLISTED": {"REJECTED"},
        "INTERVIEW": {"SELECTED", "REJECTED"},
    }
    if requested_status not in transitions.get(application.status, set()):
        raise HTTPException(status_code=400, detail=f"Cannot move an application from {application.status} to {requested_status}")
    application.status = requested_status
    db.commit()
    db.refresh(application)
    return _application_response(application, job)


@router.post("/applications/{application_id}/interview", response_model=JobApplicationResponse)
def schedule_interview(
    application_id: int,
    payload: InterviewScheduleRequest,
    db: Session = Depends(get_db),
    user: User = Depends(EMPLOYERS),
):
    application = db.get(JobApplication, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    job = db.get(JobPosting, application.job_id)
    if not job or (user.role != "NCCT_ADMIN" and job.employer_id != user.id):
        raise HTTPException(status_code=403, detail="You cannot schedule this interview")
    if application.status != "SHORTLISTED":
        raise HTTPException(status_code=400, detail="Only shortlisted applications can be scheduled for an interview")
    if payload.scheduled_at.tzinfo is None:
        raise HTTPException(status_code=400, detail="Interview time must include a timezone")
    if payload.scheduled_at <= datetime.now(payload.scheduled_at.tzinfo):
        raise HTTPException(status_code=400, detail="Interview time must be in the future")
    mode = payload.mode.upper().strip()
    if mode not in {"ONLINE", "IN_PERSON", "PHONE"}:
        raise HTTPException(status_code=400, detail="Interview mode must be ONLINE, IN_PERSON or PHONE")
    application.status = "INTERVIEW"
    application.interview_scheduled_at = payload.scheduled_at
    application.interview_mode = mode
    application.interview_location_or_link = payload.location_or_link.strip()
    application.interview_notes = payload.notes
    db.commit()
    db.refresh(application)
    return _application_response(application, job)


@router.post("/applications/{application_id}/interview/cancel", response_model=JobApplicationResponse)
def cancel_interview(
    application_id: int,
    payload: InterviewCancelRequest,
    db: Session = Depends(get_db),
    user: User = Depends(EMPLOYERS),
):
    application = db.get(JobApplication, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    job = db.get(JobPosting, application.job_id)
    if not job or (user.role != "NCCT_ADMIN" and job.employer_id != user.id):
        raise HTTPException(status_code=403, detail="You cannot cancel this interview")
    if not application.interview_scheduled_at:
        raise HTTPException(status_code=400, detail="No interview is scheduled")
    application.interview_scheduled_at = None
    application.interview_mode = None
    application.interview_location_or_link = None
    application.interview_notes = payload.reason
    if application.status == "INTERVIEW":
        application.status = "SHORTLISTED"
    db.commit()
    db.refresh(application)
    return _application_response(application, job)


@router.post("/applications/{application_id}/offer", response_model=JobApplicationResponse)
def send_offer(
    application_id: int,
    payload: OfferCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(EMPLOYERS),
):
    application = db.get(JobApplication, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    job = db.get(JobPosting, application.job_id)
    if not job or (user.role != "NCCT_ADMIN" and job.employer_id != user.id):
        raise HTTPException(status_code=403, detail="You cannot send an offer for this application")
    if application.status != "SELECTED":
        raise HTTPException(status_code=400, detail="Candidate must be SELECTED before an offer can be sent")
    if payload.expires_at and payload.expires_at.tzinfo is None:
        raise HTTPException(status_code=400, detail="Offer expiry must include a timezone")
    if payload.expires_at and payload.expires_at <= datetime.now(payload.expires_at.tzinfo):
        raise HTTPException(status_code=400, detail="Offer expiry must be in the future")
    application.offer_status = "PENDING"
    application.offer_offered_at = datetime.now(payload.expires_at.tzinfo) if payload.expires_at else datetime.now().astimezone()
    application.offer_expires_at = payload.expires_at
    application.offer_salary = payload.salary
    application.offer_employment_type = payload.employment_type
    application.offer_notes = payload.notes
    application.offer_responded_at = None
    db.commit()
    db.refresh(application)
    return _application_response(application, job)


@router.post("/applications/{application_id}/offer/respond", response_model=JobApplicationResponse)
def respond_to_offer(
    application_id: int,
    payload: OfferResponseRequest,
    db: Session = Depends(get_db),
    user: User = Depends(TRAINEES),
):
    application = db.get(JobApplication, application_id)
    if not application or application.trainee_id != user.id:
        raise HTTPException(status_code=404, detail="Application not found")
    job = db.get(JobPosting, application.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if application.offer_status != "PENDING":
        raise HTTPException(status_code=400, detail="There is no pending offer to respond to")
    decision = payload.decision.upper().strip()
    if decision not in {"ACCEPT", "DECLINE"}:
        raise HTTPException(status_code=400, detail="Decision must be ACCEPT or DECLINE")
    if application.offer_expires_at and application.offer_expires_at <= datetime.now(application.offer_expires_at.tzinfo):
        application.offer_status = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=400, detail="This offer has expired")
    application.offer_status = "ACCEPTED" if decision == "ACCEPT" else "DECLINED"
    application.offer_responded_at = datetime.now(application.offer_expires_at.tzinfo) if application.offer_expires_at else datetime.now().astimezone()
    if decision == "ACCEPT":
        application.status = "SELECTED"
        existing_outcome = db.scalar(select(EmploymentOutcome).where(EmploymentOutcome.application_id == application.id))
        if not existing_outcome:
            db.add(EmploymentOutcome(
                application_id=application.id, trainee_id=application.trainee_id,
                employer_id=job.employer_id, status="PENDING_JOINING",
            ))
    db.commit()
    db.refresh(application)
    return _application_response(application, job)


@router.post("/applications/{application_id}/placement", response_model=PlacementResponse)
def update_placement(
    application_id: int,
    payload: PlacementUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(EMPLOYERS),
):
    application = db.get(JobApplication, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    job = db.get(JobPosting, application.job_id)
    if not job or (user.role != "NCCT_ADMIN" and job.employer_id != user.id):
        raise HTTPException(status_code=403, detail="You cannot update this placement")
    if application.offer_status != "ACCEPTED":
        raise HTTPException(status_code=400, detail="Placement can be updated only after the trainee accepts the offer")
    status = payload.status.upper().strip()
    if status not in {"PENDING_JOINING", "JOINED", "NOT_JOINED"}:
        raise HTTPException(status_code=400, detail="Status must be PENDING_JOINING, JOINED or NOT_JOINED")
    if status == "JOINED" and not payload.joining_date:
        raise HTTPException(status_code=400, detail="Joining date is required when marking the trainee as JOINED")
    outcome = db.scalar(select(EmploymentOutcome).where(EmploymentOutcome.application_id == application.id))
    if not outcome:
        outcome = EmploymentOutcome(application_id=application.id, trainee_id=application.trainee_id, employer_id=job.employer_id)
        db.add(outcome)
    outcome.status = status
    outcome.joining_date = payload.joining_date if status == "JOINED" else None
    outcome.notes = payload.notes
    outcome.updated_by_id = user.id
    db.commit()
    db.refresh(outcome)
    return _placement_response(outcome, application, job)


@router.get("/placements", response_model=list[PlacementResponse])
def list_placements(db: Session = Depends(get_db), user: User = Depends(EMPLOYERS)):
    query = (select(EmploymentOutcome, JobApplication, JobPosting)
        .join(JobApplication, JobApplication.id == EmploymentOutcome.application_id)
        .join(JobPosting, JobPosting.id == JobApplication.job_id)
        .order_by(EmploymentOutcome.updated_at.desc()))
    if user.role != "NCCT_ADMIN":
        query = query.where(EmploymentOutcome.employer_id == user.id)
    return [_placement_response(o, a, j) for o, a, j in db.execute(query).all()]


@router.get("/placement-summary", response_model=PlacementSummary)
def placement_summary(db: Session = Depends(get_db), user: User = Depends(EMPLOYERS)):
    query = select(EmploymentOutcome)
    if user.role != "NCCT_ADMIN":
        query = query.where(EmploymentOutcome.employer_id == user.id)
    rows = db.scalars(query).all()
    return PlacementSummary(
        total=len(rows),
        pending_joining=sum(1 for x in rows if x.status == "PENDING_JOINING"),
        joined=sum(1 for x in rows if x.status == "JOINED"),
        not_joined=sum(1 for x in rows if x.status == "NOT_JOINED"),
    )


@router.get("/placement-analytics", response_model=PlacementAnalytics)
def placement_analytics(db: Session = Depends(get_db), user: User = Depends(EMPLOYERS)):
    jobs_query = select(JobPosting)
    apps_query = select(JobApplication, JobPosting).join(JobPosting, JobPosting.id == JobApplication.job_id)
    outcomes_query = select(EmploymentOutcome)
    if user.role != "NCCT_ADMIN":
        jobs_query = jobs_query.where(JobPosting.employer_id == user.id)
        apps_query = apps_query.where(JobPosting.employer_id == user.id)
        outcomes_query = outcomes_query.where(EmploymentOutcome.employer_id == user.id)
    jobs = db.scalars(jobs_query).all()
    applications = [row[0] for row in db.execute(apps_query).all()]
    outcomes = db.scalars(outcomes_query).all()
    offers_pending = sum(1 for a in applications if a.offer_status == "PENDING")
    offers_accepted = sum(1 for a in applications if a.offer_status == "ACCEPTED")
    offers_declined = sum(1 for a in applications if a.offer_status == "DECLINED")
    joined = sum(1 for o in outcomes if o.status == "JOINED")
    accepted = offers_accepted
    join_rate = round((joined / accepted) * 100, 1) if accepted else 0.0
    return PlacementAnalytics(
        jobs_total=len(jobs),
        jobs_published=sum(1 for j in jobs if j.status == "PUBLISHED"),
        applications_total=len(applications),
        applications_shortlisted=sum(1 for a in applications if a.status == "SHORTLISTED"),
        applications_interview=sum(1 for a in applications if a.status == "INTERVIEW"),
        applications_selected=sum(1 for a in applications if a.status == "SELECTED"),
        applications_rejected=sum(1 for a in applications if a.status == "REJECTED"),
        offers_pending=offers_pending,
        offers_accepted=offers_accepted,
        offers_declined=offers_declined,
        placements_total=len(outcomes),
        pending_joining=sum(1 for o in outcomes if o.status == "PENDING_JOINING"),
        joined=joined,
        not_joined=sum(1 for o in outcomes if o.status == "NOT_JOINED"),
        placement_join_rate=join_rate,
    )


@router.get("/placements/{placement_id}/follow-ups", response_model=list[EmploymentFollowUpResponse])
def list_follow_ups(placement_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    placement = db.get(EmploymentOutcome, placement_id)
    if not placement:
        raise HTTPException(status_code=404, detail="Placement not found")
    if user.role == "TRAINEE" and placement.trainee_id != user.id:
        raise HTTPException(status_code=403, detail="You cannot view this placement")
    if user.role == "EMPLOYER" and placement.employer_id != user.id:
        raise HTTPException(status_code=403, detail="You cannot view this placement")
    if user.role not in {"TRAINEE", "EMPLOYER", "NCCT_ADMIN"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    rows = db.scalars(select(EmploymentFollowUp).where(EmploymentFollowUp.placement_id == placement_id).order_by(EmploymentFollowUp.checked_at.desc())).all()
    return [_followup_response(row) for row in rows]


@router.post("/placements/{placement_id}/follow-ups", response_model=EmploymentFollowUpResponse)
def save_follow_up(
    placement_id: int, payload: EmploymentFollowUpRequest, db: Session = Depends(get_db), user: User = Depends(EMPLOYERS),
):
    placement = db.get(EmploymentOutcome, placement_id)
    if not placement:
        raise HTTPException(status_code=404, detail="Placement not found")
    if user.role != "NCCT_ADMIN" and placement.employer_id != user.id:
        raise HTTPException(status_code=403, detail="You cannot update this placement")
    if placement.status != "JOINED":
        raise HTTPException(status_code=400, detail="Follow-up is available only for JOINED placements")
    checkpoint = payload.checkpoint.upper().strip()
    if checkpoint not in {"30_DAY", "90_DAY", "180_DAY"}:
        raise HTTPException(status_code=400, detail="Checkpoint must be 30_DAY, 90_DAY or 180_DAY")
    status = payload.status.upper().strip()
    if status not in {"CONTINUING", "LEFT", "ON_HOLD"}:
        raise HTTPException(status_code=400, detail="Status must be CONTINUING, LEFT or ON_HOLD")
    row = db.scalar(select(EmploymentFollowUp).where(EmploymentFollowUp.placement_id == placement_id, EmploymentFollowUp.checkpoint == checkpoint))
    if not row:
        row = EmploymentFollowUp(placement_id=placement.id, trainee_id=placement.trainee_id, employer_id=placement.employer_id, checkpoint=checkpoint)
        db.add(row)
    row.status = status
    row.notes = payload.notes
    row.employer_feedback = payload.employer_feedback
    row.trainee_feedback = payload.trainee_feedback
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return _followup_response(row)


@router.get("/my-placement-follow-ups", response_model=list[EmploymentFollowUpResponse])
def my_follow_ups(db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    rows = db.scalars(select(EmploymentFollowUp).where(EmploymentFollowUp.trainee_id == user.id).order_by(EmploymentFollowUp.checked_at.desc())).all()
    return [_followup_response(row) for row in rows]

@router.get("/my-placement", response_model=list[PlacementResponse])
def my_placement(db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    query = (select(EmploymentOutcome, JobApplication, JobPosting)
        .join(JobApplication, JobApplication.id == EmploymentOutcome.application_id)
        .join(JobPosting, JobPosting.id == JobApplication.job_id)
        .where(EmploymentOutcome.trainee_id == user.id)
        .order_by(EmploymentOutcome.updated_at.desc()))
    return [_placement_response(o, a, j) for o, a, j in db.execute(query).all()]
