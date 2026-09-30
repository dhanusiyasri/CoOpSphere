import io
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.careers.models import JobPosting, JobApplication
from app.careers.profile_models import CareerProfile
from app.careers.profile_schemas import (
    CandidateProfileResponse,
    CareerProfileResponse,
    CareerProfileUpdate,
    RecommendedJobResponse,
    CandidateSearchResponse,
)
from app.training.models import ParticipantProfile
from app.credentials.models import Credential
from app.users.models import User

router = APIRouter(prefix="/careers", tags=["Career Profiles & Matching"])
TRAINEES = require_roles("TRAINEE")
EMPLOYERS = require_roles("EMPLOYER", "NCCT_ADMIN")


def _tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    return {t for t in re.split(r"[,;|/]+", value.lower()) if t.strip()}


def _get_profile(db: Session, trainee_id: int) -> CareerProfile:
    profile = db.scalar(select(CareerProfile).where(CareerProfile.trainee_id == trainee_id))
    if not profile:
        profile = CareerProfile(trainee_id=trainee_id, profile_visibility="VISIBLE")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def _education_match(profile_level: str | None, required: str | None) -> bool:
    if not required:
        return True
    if not profile_level:
        return False
    p = profile_level.lower()
    r = required.lower()
    education_order = {
        "secondary": 1, "higher secondary": 2, "diploma": 3,
        "graduate": 4, "postgraduate": 5, "doctorate": 6,
    }
    p_score = next((v for k, v in education_order.items() if k in p), 0)
    r_score = next((v for k, v in education_order.items() if k in r), 0)
    return p_score >= r_score if r_score else r in p


def _match_job(job: JobPosting, profile: CareerProfile, participant: ParticipantProfile | None) -> RecommendedJobResponse:
    profile_skills = _tokens(profile.skills)
    job_skills = _tokens(job.skills)
    matched = sorted(profile_skills & job_skills)

    score = 0
    reasons: list[str] = []
    if job_skills:
        skill_score = round(60 * len(matched) / len(job_skills))
        score += skill_score
        if matched:
            reasons.append(f"{len(matched)} skill match{'es' if len(matched) != 1 else ''}")
    else:
        score += 60
        reasons.append("No specific skills required")

    experience = participant.years_experience if participant else 0
    if experience >= job.minimum_experience_years:
        score += 20
        reasons.append("Experience requirement met")
    elif job.minimum_experience_years == 0:
        score += 20
    else:
        reasons.append("Experience requirement not yet met")

    if _education_match(participant.education_level if participant else None, job.minimum_education):
        score += 10
        if job.minimum_education:
            reasons.append("Education requirement met")
    elif job.minimum_education:
        reasons.append("Education requirement may need review")

    preferred_locations = _tokens(profile.preferred_locations)
    if not preferred_locations or job.location.lower() in preferred_locations or any(
        p in job.location.lower() or job.location.lower() in p for p in preferred_locations
    ):
        score += 5
        reasons.append("Location preference matches")

    preferred_types = _tokens(profile.preferred_employment_types)
    if not preferred_types or job.employment_type.lower() in preferred_types or job.employment_type.lower().replace("_", " ") in preferred_types:
        score += 5
        reasons.append("Employment preference matches")

    return RecommendedJobResponse(
        job_id=job.id,
        title=job.title,
        organization_name=job.organization_name,
        location=job.location,
        employment_type=job.employment_type,
        skills=job.skills,
        minimum_education=job.minimum_education,
        minimum_experience_years=job.minimum_experience_years,
        salary_range=job.salary_range,
        match_score=min(score, 100),
        matched_skills=matched,
        reasons=reasons,
    )


@router.get("/profile", response_model=CareerProfileResponse)
def get_my_career_profile(db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    return _get_profile(db, user.id)


@router.put("/profile", response_model=CareerProfileResponse)
def update_my_career_profile(
    payload: CareerProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(TRAINEES),
):
    profile = _get_profile(db, user.id)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/recommended-jobs", response_model=list[RecommendedJobResponse])
def recommended_jobs(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(TRAINEES),
):
    profile = _get_profile(db, user.id)
    participant = db.scalar(select(ParticipantProfile).where(ParticipantProfile.user_id == user.id))
    jobs = db.scalars(select(JobPosting).where(JobPosting.status == "PUBLISHED").order_by(JobPosting.created_at.desc())).all()
    applications = set(db.scalars(select(JobApplication.job_id).where(JobApplication.trainee_id == user.id)).all())
    results = [_match_job(job, profile, participant) for job in jobs if job.id not in applications]
    results.sort(key=lambda item: (-item.match_score, item.job_id))
    return results[:limit]


@router.get("/applications/{application_id}/candidate-profile", response_model=CandidateProfileResponse)
def candidate_profile(
    application_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(EMPLOYERS),
):
    application = db.get(JobApplication, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    job = db.get(JobPosting, application.job_id)
    if not job or (user.role != "NCCT_ADMIN" and job.employer_id != user.id):
        raise HTTPException(status_code=403, detail="You cannot view this candidate")

    trainee = db.get(User, application.trainee_id)
    participant = db.scalar(select(ParticipantProfile).where(ParticipantProfile.user_id == application.trainee_id))
    profile = _get_profile(db, application.trainee_id)
    if profile.profile_visibility == "HIDDEN" and user.role != "NCCT_ADMIN":
        raise HTTPException(status_code=403, detail="Candidate profile is not visible")

    return CandidateProfileResponse(
        trainee_id=trainee.id,
        full_name=trainee.full_name,
        email=trainee.email,
        participant_code=participant.participant_code if participant else None,
        phone=participant.phone if participant else None,
        designation=participant.designation if participant else None,
        organization_name=participant.organization_name if participant else None,
        education_level=participant.education_level if participant else None,
        district=participant.district if participant else None,
        state=participant.state if participant else None,
        digital_literacy_level=participant.digital_literacy_level if participant else None,
        years_experience=participant.years_experience if participant else 0,
        headline=profile.headline,
        professional_summary=profile.professional_summary,
        skills=profile.skills,
        preferred_locations=profile.preferred_locations,
        preferred_employment_types=profile.preferred_employment_types,
        resume_text=profile.resume_text,
    )


def _build_resume_pdf(user: User, profile: CareerProfile, participant: ParticipantProfile | None, credentials: list[Credential]) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Resume PDF dependency is not installed. Run pip install -r requirements.txt.") from exc

    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    left = 22 * mm
    y = height - 24 * mm

    def line(text: str, font="Helvetica", size=10, gap=6):
        nonlocal y
        if y < 25 * mm:
            pdf.showPage()
            y = height - 24 * mm
        pdf.setFont(font, size)
        pdf.drawString(left, y, text[:115])
        y -= gap * mm

    pdf.setTitle(f"NCCT Resume - {user.full_name}")
    line("NATIONAL COUNCIL FOR COOPERATIVE TRAINING", "Helvetica-Bold", 12, 8)
    line(user.full_name, "Helvetica-Bold", 20, 10)
    if profile.headline:
        line(profile.headline, "Helvetica", 11, 7)
    line(user.email, "Helvetica", 9, 6)
    if participant and participant.phone:
        line(participant.phone, "Helvetica", 9, 6)
    location = ", ".join([v for v in [participant.district if participant else None, participant.state if participant else None] if v])
    if location:
        line(location, "Helvetica", 9, 9)

    def section(title: str, body: str | None):
        nonlocal y
        y -= 3 * mm
        line(title.upper(), "Helvetica-Bold", 11, 7)
        if body:
            for paragraph in body.splitlines() or [body]:
                line(paragraph.strip(), "Helvetica", 9, 5)
        y -= 2 * mm

    section("Professional Summary", profile.professional_summary)
    section("Skills", profile.skills)
    if participant:
        details = f"Education: {participant.education_level or 'Not provided'} | Experience: {participant.years_experience} years | Digital literacy: {participant.digital_literacy_level or 'Not provided'}"
        section("Experience & Education", details)
    section("Resume / Experience Summary", profile.resume_text)
    if credentials:
        body = "\n".join(f"{c.course_title} — {c.score_percentage}% — {c.credential_number} — {c.issued_at.strftime('%d %b %Y')}" for c in credentials)
        section("NCCT Credentials", body)

    pdf.setFont("Helvetica", 7)
    pdf.drawString(left, 12 * mm, "Generated from the NCCT Cooperative Employment Exchange")
    pdf.save()
    return output.getvalue()


@router.get("/profile/resume.pdf")
def download_my_resume(db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    from fastapi.responses import Response
    profile = _get_profile(db, user.id)
    participant = db.scalar(select(ParticipantProfile).where(ParticipantProfile.user_id == user.id))
    credentials = db.scalars(select(Credential).where(Credential.trainee_id == user.id, Credential.status == "ISSUED").order_by(Credential.issued_at.desc())).all()
    pdf = _build_resume_pdf(user, profile, participant, credentials)
    filename = f"NCCT-Resume-{re.sub(r'[^A-Za-z0-9]+', '-', user.full_name).strip('-') or 'trainee'}.pdf"
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/candidate-search", response_model=list[CandidateSearchResponse])
def candidate_search(
    query: str | None = Query(default=None, max_length=100),
    skill: str | None = Query(default=None, max_length=100),
    location: str | None = Query(default=None, max_length=100),
    min_experience: int = Query(default=0, ge=0, le=60),
    education: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(EMPLOYERS),
):
    stmt = (
        select(CareerProfile, User, ParticipantProfile)
        .join(User, User.id == CareerProfile.trainee_id)
        .outerjoin(ParticipantProfile, ParticipantProfile.user_id == User.id)
        .where(CareerProfile.profile_visibility == "VISIBLE", User.role == "TRAINEE")
    )
    if query:
        q = f"%{query.strip()}%"
        stmt = stmt.where(or_(User.full_name.ilike(q), CareerProfile.headline.ilike(q), CareerProfile.professional_summary.ilike(q)))
    if skill:
        stmt = stmt.where(CareerProfile.skills.ilike(f"%{skill.strip()}%"))
    if location:
        loc = f"%{location.strip()}%"
        stmt = stmt.where(or_(ParticipantProfile.district.ilike(loc), ParticipantProfile.state.ilike(loc), CareerProfile.preferred_locations.ilike(loc)))
    if min_experience:
        stmt = stmt.where(ParticipantProfile.years_experience >= min_experience)
    if education:
        stmt = stmt.where(ParticipantProfile.education_level.ilike(f"%{education.strip()}%"))

    rows = db.execute(stmt.order_by(User.full_name.asc()).limit(limit)).all()
    result = []
    for profile, trainee, participant in rows:
        credential_count = db.scalar(select(func.count(Credential.id)).where(Credential.trainee_id == trainee.id, Credential.status == "ISSUED")) or 0
        result.append(CandidateSearchResponse(
            trainee_id=trainee.id,
            full_name=trainee.full_name,
            headline=profile.headline,
            email=trainee.email,
            phone=participant.phone if participant else None,
            education_level=participant.education_level if participant else None,
            years_experience=participant.years_experience if participant else 0,
            district=participant.district if participant else None,
            state=participant.state if participant else None,
            skills=profile.skills,
            digital_literacy_level=participant.digital_literacy_level if participant else None,
            credential_count=int(credential_count),
            profile_visibility=profile.profile_visibility,
        ))
    return result


@router.get("/candidate-search/{trainee_id}", response_model=CandidateProfileResponse)
def search_candidate_profile(trainee_id: int, db: Session = Depends(get_db), user: User = Depends(EMPLOYERS)):
    trainee = db.get(User, trainee_id)
    if not trainee or trainee.role != "TRAINEE":
        raise HTTPException(status_code=404, detail="Candidate not found")
    profile = _get_profile(db, trainee_id)
    if profile.profile_visibility != "VISIBLE" and user.role != "NCCT_ADMIN":
        raise HTTPException(status_code=403, detail="Candidate profile is not visible")
    participant = db.scalar(select(ParticipantProfile).where(ParticipantProfile.user_id == trainee_id))
    return CandidateProfileResponse(
        trainee_id=trainee.id, full_name=trainee.full_name, email=trainee.email,
        participant_code=participant.participant_code if participant else None,
        phone=participant.phone if participant else None, designation=participant.designation if participant else None,
        organization_name=participant.organization_name if participant else None, education_level=participant.education_level if participant else None,
        district=participant.district if participant else None, state=participant.state if participant else None,
        digital_literacy_level=participant.digital_literacy_level if participant else None,
        years_experience=participant.years_experience if participant else 0,
        headline=profile.headline, professional_summary=profile.professional_summary, skills=profile.skills,
        preferred_locations=profile.preferred_locations, preferred_employment_types=profile.preferred_employment_types,
        resume_text=profile.resume_text,
    )
