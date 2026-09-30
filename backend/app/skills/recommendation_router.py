from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.users.models import User
from app.training.models import ParticipantProfile, TrainingCourse
from app.careers.models import JobPosting
from app.skills.passport_models import SkillCatalog, TraineeSkill
from app.skills.passport_router import _scope_user_ids
from app.skills.recommendation_schemas import (
    SkillGapItem, LearningRecommendation, JobRecommendation, SkillRecommendations,
)

router = APIRouter(prefix="/skills/recommendations", tags=["Skill Recommendations"])
MANAGERS = require_roles("NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER")
TRAINEE = require_roles("TRAINEE")


def _build(db: Session, trainee: User) -> SkillRecommendations:
    profile = db.scalar(select(ParticipantProfile).where(ParticipantProfile.user_id == trainee.id))
    rows = db.execute(
        select(TraineeSkill, SkillCatalog)
        .join(SkillCatalog, SkillCatalog.id == TraineeSkill.skill_id)
        .where(TraineeSkill.trainee_id == trainee.id, SkillCatalog.active == True)
    ).all()
    by_code = {skill.code: row.proficiency for row, skill in rows}
    by_name = {skill.name.lower(): row.proficiency for row, skill in rows}
    catalog = db.scalars(select(SkillCatalog).where(SkillCatalog.active == True)).all()
    gaps = []
    for skill in catalog:
        current = by_code.get(skill.code, 0)
        if current < 3:
            gaps.append(SkillGapItem(
                skill_id=skill.id, code=skill.code, name=skill.name,
                category=skill.category, current_proficiency=current,
                target_proficiency=3, gap=max(0, 3-current),
            ))
    gap_terms = [(g.name.lower(), g.category.lower(), g.code.lower()) for g in gaps]

    courses = db.scalars(
        select(TrainingCourse).where(TrainingCourse.status == "PUBLISHED").order_by(TrainingCourse.title)
    ).all()
    course_recs = []
    for course in courses:
        hay = " ".join([course.title or "", course.description or "", course.category or "", course.level or ""]).lower()
        matched = []
        for name, category, code in gap_terms:
            if name in hay or category in hay or code.replace("_", " ") in hay:
                matched.append(next(g.name for g in gaps if g.name.lower() == name))
        if matched:
            score = min(99, 60 + len(matched) * 12)
            course_recs.append(LearningRecommendation(
                course_id=course.id, course_code=course.course_code, title=course.title,
                category=course.category, level=course.level, delivery_mode=course.delivery_mode,
                match_score=score, matched_skills=matched[:4],
                reason=f"Addresses {', '.join(matched[:3])} skill gap(s).",
            ))
    course_recs.sort(key=lambda x: (-x.match_score, x.title))

    jobs = db.scalars(select(JobPosting).where(JobPosting.status == "PUBLISHED").order_by(JobPosting.created_at.desc())).all()
    job_recs = []
    for job in jobs:
        hay = " ".join([job.title or "", job.description or "", job.skills or "", job.minimum_education or ""]).lower()
        matched = []
        missing = []
        for g in gaps:
            name = g.name.lower()
            if name in hay or g.category.lower() in hay or g.code.lower().replace("_", " ") in hay:
                matched.append(g.name)
            elif g.gap >= 2:
                missing.append(g.name)
        if matched:
            score = min(98, 55 + len(matched) * 10 - min(15, len(missing) * 3))
            job_recs.append(JobRecommendation(
                job_id=job.id, title=job.title, organization_name=job.organization_name,
                location=job.location, employment_type=job.employment_type,
                match_score=max(40, score), matched_skills=matched[:5], missing_skills=missing[:4],
                reason=f"Matches {', '.join(matched[:3])} from your current skill profile.",
            ))
    job_recs.sort(key=lambda x: (-x.match_score, x.title))

    return SkillRecommendations(
        trainee_id=trainee.id, trainee_name=trainee.full_name,
        digital_literacy_level=profile.digital_literacy_level if profile else "BASIC",
        skill_gaps=gaps, learning_recommendations=course_recs[:6], job_recommendations=job_recs[:6],
    )


@router.get("/my", response_model=SkillRecommendations)
def my_recommendations(db: Session = Depends(get_db), user: User = Depends(TRAINEE)):
    return _build(db, user)


@router.get("/{trainee_id}", response_model=SkillRecommendations)
def trainee_recommendations(trainee_id: int, db: Session = Depends(get_db), manager: User = Depends(MANAGERS)):
    trainee = db.get(User, trainee_id)
    if not trainee or trainee.role != "TRAINEE" or not trainee.is_active:
        raise HTTPException(status_code=404, detail="Trainee not found")
    allowed = _scope_user_ids(db, manager)
    if allowed is not None and trainee_id not in allowed:
        raise HTTPException(status_code=403, detail="Trainee is outside your role scope")
    return _build(db, trainee)
