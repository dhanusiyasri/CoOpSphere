import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.training.models import ParticipantProfile
from app.users.models import User
from app.skills.models import DigitalLiteracyAttempt
from app.skills.schemas import DigitalLiteracyQuestion, DigitalLiteracyAttemptCreate, DigitalLiteracyAttemptResponse, DigitalLiteracyResult

router = APIRouter(prefix="/skills/digital-literacy", tags=["Digital Literacy"])
MANAGERS = require_roles("NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER")

QUESTIONS = [
    {"id":"q1","question":"Which action is safest when you receive an unexpected email asking for your password?","options":["Reply with the password","Click the link immediately","Do not share it and verify the sender through a trusted channel","Forward it to everyone"]},
    {"id":"q2","question":"Which application is commonly used to create and edit spreadsheets?","options":["Spreadsheet software","Image viewer","Media player","Calculator only"]},
    {"id":"q3","question":"What is a strong password practice?","options":["Reuse one password everywhere","Use a long unique password or passphrase","Share it with a colleague","Write it on a public notice board"]},
    {"id":"q4","question":"What should you do before opening a file from an unknown source?","options":["Open it immediately","Verify the source and scan it if appropriate","Disable security tools","Rename it and open it"]},
    {"id":"q5","question":"Which is an example of cloud storage?","options":["A remote online file storage service","A paper notebook","A keyboard","A printer cable"]},
    {"id":"q6","question":"What does a web browser primarily help you do?","options":["Access websites and web applications","Charge a phone","Print electricity bills automatically","Repair hardware"]},
    {"id":"q7","question":"Why should important work files be backed up?","options":["To make the computer slower","To recover data after loss or device failure","To remove all security","To avoid using folders"]},
    {"id":"q8","question":"What is the best way to share sensitive trainee data?","options":["Public social media","An approved secure channel with only authorized recipients","An open group chat","A public spreadsheet link"]},
    {"id":"q9","question":"What does a video meeting link usually provide?","options":["A way to join an online meeting","A bank account number","A printer driver","A password recovery code"]},
    {"id":"q10","question":"If a website address begins with HTTPS, what does it generally indicate?","options":["The connection is using encryption in transit","The site is guaranteed trustworthy","The computer has no malware","The page is always free"]},
]
ANSWERS = {"q1":2,"q2":0,"q3":1,"q4":1,"q5":0,"q6":0,"q7":1,"q8":1,"q9":0,"q10":0}

def level_for(pct: int) -> str:
    if pct >= 80: return "ADVANCED"
    if pct >= 60: return "INTERMEDIATE"
    return "BASIC"

def response(row, user):
    return DigitalLiteracyAttemptResponse(id=row.id, trainee_id=row.trainee_id, trainee_name=user.full_name, trainee_email=user.email, score=row.score, total_questions=row.total_questions, percentage=row.percentage, level=row.level, completed_at=row.completed_at)

@router.get("/questions", response_model=list[DigitalLiteracyQuestion])
def questions(_: User = Depends(get_current_user)):
    return [DigitalLiteracyQuestion(id=q["id"], question=q["question"], options=q["options"]) for q in QUESTIONS]

@router.post("/attempts", response_model=DigitalLiteracyResult, status_code=status.HTTP_201_CREATED)
def submit_attempt(payload: DigitalLiteracyAttemptCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("TRAINEE"))):
    if set(payload.answers) != set(ANSWERS):
        raise HTTPException(400, "Please answer all digital literacy questions")
    if any(not isinstance(v, int) or v < 0 or v > 3 for v in payload.answers.values()):
        raise HTTPException(400, "Invalid answer selection")
    score = sum(payload.answers[k] == correct for k, correct in ANSWERS.items())
    total = len(ANSWERS)
    pct = round(score * 100 / total)
    level = level_for(pct)
    row = DigitalLiteracyAttempt(trainee_id=user.id, score=score, total_questions=total, percentage=pct, level=level, answers_json=json.dumps(payload.answers, sort_keys=True))
    db.add(row)
    profile = db.scalar(select(ParticipantProfile).where(ParticipantProfile.user_id == user.id))
    if profile:
        profile.digital_literacy_level = level
        profile.profile_status = "COMPLETE" if profile.profile_status == "INCOMPLETE" else profile.profile_status
    db.commit(); db.refresh(row)
    return DigitalLiteracyResult(score=row.score, total_questions=row.total_questions, percentage=row.percentage, level=row.level, completed_at=row.completed_at)

@router.get("/my-attempts", response_model=list[DigitalLiteracyAttemptResponse])
def my_attempts(db: Session = Depends(get_db), user: User = Depends(require_roles("TRAINEE"))):
    rows = db.scalars(select(DigitalLiteracyAttempt).where(DigitalLiteracyAttempt.trainee_id == user.id).order_by(DigitalLiteracyAttempt.completed_at.desc())).all()
    return [response(r, user) for r in rows]

@router.get("/attempts", response_model=list[DigitalLiteracyAttemptResponse])
def manager_attempts(db: Session = Depends(get_db), user: User = Depends(MANAGERS)):
    q = select(DigitalLiteracyAttempt, User).join(User, User.id == DigitalLiteracyAttempt.trainee_id)
    if user.role == "TRAINER":
        from app.training.models import Enrollment, TrainingBatch
        q = q.join(Enrollment, Enrollment.trainee_id == User.id).join(TrainingBatch, TrainingBatch.id == Enrollment.batch_id).where(TrainingBatch.trainer_id == user.id)
    elif user.role == "INSTITUTE_ADMIN":
        from app.training.models import Enrollment, TrainingBatch, TrainingProgramme
        q = q.join(Enrollment, Enrollment.trainee_id == User.id).join(TrainingBatch, TrainingBatch.id == Enrollment.batch_id).join(TrainingProgramme, TrainingProgramme.id == TrainingBatch.programme_id).where(TrainingProgramme.institution_id == user.institution_id)
    rows = db.execute(q.order_by(DigitalLiteracyAttempt.completed_at.desc())).all()
    return [response(r,u) for r,u in rows]
