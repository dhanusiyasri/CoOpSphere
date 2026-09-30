from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.users.models import User
from app.training.models import ParticipantProfile
from app.skills.passport_models import SkillCatalog, TraineeSkill
from app.skills.passport_schemas import SkillCatalogResponse, SkillAssignmentCreate, SkillItem, SkillGap, SkillPassport

router = APIRouter(prefix="/skills/passport", tags=["Skill Passport"])
MANAGERS = require_roles("NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER")

LEVELS = {1: "FOUNDATION", 2: "BASIC", 3: "WORKING", 4: "PROFICIENT", 5: "ADVANCED"}

def _scope_user_ids(db: Session, current: User):
    if current.role == "NCCT_ADMIN":
        return None
    from app.training.models import Enrollment, TrainingBatch, TrainingProgramme
    q = select(Enrollment.trainee_id).join(TrainingBatch, TrainingBatch.id == Enrollment.batch_id).join(TrainingProgramme, TrainingProgramme.id == TrainingBatch.programme_id).where(Enrollment.status == "ACTIVE")
    if current.role == "TRAINER": q = q.where(TrainingBatch.trainer_id == current.id)
    else: q = q.where(TrainingProgramme.institution_id == current.institution_id)
    return set(db.scalars(q).all())

def _passport(db: Session, trainee: User) -> SkillPassport:
    profile = db.scalar(select(ParticipantProfile).where(ParticipantProfile.user_id == trainee.id))
    rows = db.execute(select(TraineeSkill, SkillCatalog).join(SkillCatalog, SkillCatalog.id == TraineeSkill.skill_id).where(TraineeSkill.trainee_id == trainee.id, SkillCatalog.active == True).order_by(SkillCatalog.category, SkillCatalog.name)).all()
    skills = [SkillItem(id=r.id, skill_id=s.id, code=s.code, name=s.name, category=s.category, proficiency=r.proficiency, proficiency_label=LEVELS.get(r.proficiency, "UNKNOWN"), evidence_type=r.evidence_type, evidence_note=r.evidence_note, updated_at=r.updated_at) for r,s in rows]
    by_id = {r.skill_id: r.proficiency for r in [x[0] for x in rows]}
    catalog = db.scalars(select(SkillCatalog).where(SkillCatalog.active == True).order_by(SkillCatalog.category, SkillCatalog.name)).all()
    gaps = [SkillGap(skill_id=s.id, code=s.code, name=s.name, category=s.category, current_proficiency=by_id.get(s.id, 0), target_proficiency=3, gap=max(0, 3-by_id.get(s.id, 0))) for s in catalog if by_id.get(s.id, 0) < 3]
    return SkillPassport(trainee_id=trainee.id, trainee_name=trainee.full_name, trainee_email=trainee.email, digital_literacy_level=profile.digital_literacy_level if profile else "BASIC", skills=skills, skill_gaps=gaps, total_skills=len(skills), verified_skills=sum(1 for x in skills if x.evidence_type in {"TRAINER_VERIFIED", "ASSESSMENT"}))

@router.get("/catalog", response_model=list[SkillCatalogResponse])
def catalog(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.scalars(select(SkillCatalog).where(SkillCatalog.active == True).order_by(SkillCatalog.category, SkillCatalog.name)).all()

@router.get("/my", response_model=SkillPassport)
def my_passport(db: Session = Depends(get_db), user: User = Depends(require_roles("TRAINEE"))):
    return _passport(db, user)

@router.get("", response_model=list[SkillPassport])
def passports(db: Session = Depends(get_db), user: User = Depends(MANAGERS)):
    ids = _scope_user_ids(db, user)
    q = select(User).where(User.role == "TRAINEE", User.is_active == True)
    if ids is not None: q = q.where(User.id.in_(ids))
    return [_passport(db, trainee) for trainee in db.scalars(q.order_by(User.full_name)).all()]

@router.post("/assign", response_model=SkillItem, status_code=status.HTTP_201_CREATED)
def assign_skill(payload: SkillAssignmentCreate, db: Session = Depends(get_db), manager: User = Depends(MANAGERS)):
    trainee = db.get(User, payload.trainee_id)
    skill = db.get(SkillCatalog, payload.skill_id)
    if not trainee or trainee.role != "TRAINEE" or not trainee.is_active: raise HTTPException(404, "Trainee not found")
    if not skill or not skill.active: raise HTTPException(404, "Skill not found")
    allowed = _scope_user_ids(db, manager)
    if allowed is not None and trainee.id not in allowed: raise HTTPException(403, "Trainee is outside your role scope")
    row = db.scalar(select(TraineeSkill).where(TraineeSkill.trainee_id == trainee.id, TraineeSkill.skill_id == skill.id))
    if row:
        row.proficiency = payload.proficiency; row.evidence_type = payload.evidence_type; row.evidence_note = payload.evidence_note; row.verified_by_id = manager.id
        db.commit(); db.refresh(row)
        return SkillItem(id=row.id, skill_id=skill.id, code=skill.code, name=skill.name, category=skill.category, proficiency=row.proficiency, proficiency_label=LEVELS[row.proficiency], evidence_type=row.evidence_type, evidence_note=row.evidence_note, updated_at=row.updated_at)
    row = TraineeSkill(trainee_id=trainee.id, skill_id=skill.id, proficiency=payload.proficiency, evidence_type=payload.evidence_type, evidence_note=payload.evidence_note, verified_by_id=manager.id)
    db.add(row); db.commit(); db.refresh(row)
    return SkillItem(id=row.id, skill_id=skill.id, code=skill.code, name=skill.name, category=skill.category, proficiency=row.proficiency, proficiency_label=LEVELS[row.proficiency], evidence_type=row.evidence_type, evidence_note=row.evidence_note, updated_at=row.updated_at)
