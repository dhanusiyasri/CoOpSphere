from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.training.models import Enrollment, Nomination, ParticipantProfile, TrainingBatch, TrainingProgramme, TrainingCourse, CourseModule, CourseLesson
from app.training.schemas import (
    BatchCreate,
    BatchResponse,
    EnrollmentCreate,
    EnrollmentResponse,
    NominationCreate,
    NominationDecision,
    NominationResponse,
    ProgrammeCreate,
    ProgrammeResponse,
    ParticipantProfileCreate,
    ParticipantProfileResponse,
    CourseCreate, CourseResponse, CourseModuleCreate, CourseModuleResponse, CourseLessonCreate, CourseLessonResponse,
)
from app.training.service import approve_nomination, create_nomination, get_batch_or_404, get_programme_or_404, reject_nomination
from app.users.models import User
from app.institutions.models import Institution

router = APIRouter(prefix="/training", tags=["Training ERP"])

PROGRAMME_MANAGERS = require_roles("NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER")


@router.get("/programmes", response_model=list[ProgrammeResponse])
def list_programmes(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.scalars(select(TrainingProgramme).order_by(TrainingProgramme.created_at.desc())).all()


@router.post("/programmes", response_model=ProgrammeResponse, status_code=status.HTTP_201_CREATED)
def create_programme(payload: ProgrammeCreate, db: Session = Depends(get_db), current_user: User = Depends(PROGRAMME_MANAGERS)):
    institution = db.get(Institution, payload.institution_id)
    if not institution or not institution.is_active:
        raise HTTPException(status_code=400, detail="Selected training provider is not available")
    if current_user.role == "INSTITUTE_ADMIN" and current_user.institution_id != payload.institution_id:
        raise HTTPException(status_code=403, detail="You can only create programmes for your institution")
    existing = db.scalar(select(TrainingProgramme).where(TrainingProgramme.code == payload.code.strip()))
    if existing:
        raise HTTPException(status_code=409, detail="Programme code already exists")
    data = payload.model_dump()
    data["code"] = data["code"].strip()
    data["title"] = data["title"].strip()
    data["category"] = data["category"].strip()
    programme = TrainingProgramme(**data)
    db.add(programme)
    db.commit()
    db.refresh(programme)
    return programme


@router.get("/batches", response_model=list[BatchResponse])
def list_batches(programme_id: int | None = None, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    query = select(TrainingBatch).order_by(TrainingBatch.start_date.desc())
    if programme_id:
        query = query.where(TrainingBatch.programme_id == programme_id)
    return db.scalars(query).all()


@router.post("/batches", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
def create_batch(payload: BatchCreate, db: Session = Depends(get_db), _user: User = Depends(PROGRAMME_MANAGERS)):
    get_programme_or_404(db, payload.programme_id)
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="End date cannot be before start date")
    existing = db.scalar(select(TrainingBatch).where(TrainingBatch.programme_id == payload.programme_id, TrainingBatch.batch_code == payload.batch_code))
    if existing:
        raise HTTPException(status_code=409, detail="Batch code already exists for this programme")
    batch = TrainingBatch(**payload.model_dump())
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def _participant_response(profile: ParticipantProfile, user: User) -> ParticipantProfileResponse:
    data = {
        "id": profile.id,
        "user_id": profile.user_id,
        "participant_code": profile.participant_code,
        "phone": profile.phone,
        "participant_type": profile.participant_type,
        "designation": profile.designation,
        "organization_name": profile.organization_name,
        "education_level": profile.education_level,
        "district": profile.district,
        "state": profile.state,
        "digital_literacy_level": profile.digital_literacy_level,
        "years_experience": profile.years_experience,
        "profile_status": profile.profile_status,
        "user_full_name": user.full_name,
        "user_email": user.email,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }
    return ParticipantProfileResponse.model_validate(data)


@router.get("/participants", response_model=list[ParticipantProfileResponse])
def list_participants(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(ParticipantProfile, User).join(User, User.id == ParticipantProfile.user_id).where(User.role == "TRAINEE").order_by(ParticipantProfile.id.desc())
    if current_user.role == "TRAINEE":
        query = query.where(ParticipantProfile.user_id == current_user.id)
    rows = db.execute(query).all()
    return [_participant_response(profile, user) for profile, user in rows]


@router.post("/participants", response_model=ParticipantProfileResponse, status_code=status.HTTP_201_CREATED)
def create_participant_profile(payload: ParticipantProfileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "TRAINEE" and current_user.id != payload.user_id:
        raise HTTPException(status_code=403, detail="You can only create your own participant profile")
    if current_user.role not in {"TRAINEE", "NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER"}:
        raise HTTPException(status_code=403, detail="You do not have permission to create participant profiles")
    trainee = db.get(User, payload.user_id)
    if not trainee or not trainee.is_active:
        raise HTTPException(status_code=404, detail="Participant user not found")
    if trainee.role != "TRAINEE":
        raise HTTPException(status_code=400, detail="Participant profile can only be created for a TRAINEE user")
    if db.scalar(select(ParticipantProfile).where(ParticipantProfile.user_id == payload.user_id)):
        raise HTTPException(status_code=409, detail="Participant profile already exists for this user")
    if db.scalar(select(ParticipantProfile).where(ParticipantProfile.participant_code == payload.participant_code.strip())):
        raise HTTPException(status_code=409, detail="Participant code already exists")
    data = payload.model_dump()
    data["participant_code"] = data["participant_code"].strip()
    profile = ParticipantProfile(**data)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _participant_response(profile, trainee)


@router.put("/participants/{user_id}", response_model=ParticipantProfileResponse)
def update_participant_profile(user_id: int, payload: ParticipantProfileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "TRAINEE" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only update your own participant profile")
    if current_user.role not in {"TRAINEE", "NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER"}:
        raise HTTPException(status_code=403, detail="You do not have permission to update participant profiles")
    if payload.user_id != user_id:
        raise HTTPException(status_code=400, detail="Profile user ID cannot be changed")
    trainee = db.get(User, user_id)
    profile = db.scalar(select(ParticipantProfile).where(ParticipantProfile.user_id == user_id))
    if not trainee or trainee.role != "TRAINEE" or not profile:
        raise HTTPException(status_code=404, detail="Participant profile not found")
    duplicate = db.scalar(select(ParticipantProfile).where(ParticipantProfile.participant_code == payload.participant_code.strip(), ParticipantProfile.user_id != user_id))
    if duplicate:
        raise HTTPException(status_code=409, detail="Participant code already exists")
    for key, value in payload.model_dump().items():
        if key != "user_id":
            setattr(profile, key, value.strip() if isinstance(value, str) and key in {"participant_code", "phone", "participant_type", "designation", "organization_name", "education_level", "district", "state", "digital_literacy_level", "profile_status"} else value)
    db.commit()
    db.refresh(profile)
    return _participant_response(profile, trainee)


@router.get("/nominations", response_model=list[NominationResponse])
def list_nominations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Nomination).order_by(Nomination.created_at.desc())
    if current_user.role == "TRAINEE":
        query = query.where(Nomination.trainee_id == current_user.id)
    return db.scalars(query).all()


@router.post("/nominations", response_model=NominationResponse, status_code=status.HTTP_201_CREATED)
def create_nomination_endpoint(payload: NominationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trainee_id = current_user.id if current_user.role == "TRAINEE" else payload.trainee_id
    return create_nomination(db, payload.batch_id, trainee_id, current_user.id, payload.remarks)


@router.post("/nominations/{nomination_id}/approve", response_model=EnrollmentResponse)
def approve_nomination_endpoint(nomination_id: int, db: Session = Depends(get_db), _user: User = Depends(PROGRAMME_MANAGERS)):
    return approve_nomination(db, nomination_id)

@router.post("/nominations/{nomination_id}/reject", response_model=NominationResponse)
def reject_nomination_endpoint(nomination_id: int, payload: NominationDecision, db: Session = Depends(get_db), _user: User = Depends(PROGRAMME_MANAGERS)):
    return reject_nomination(db, nomination_id, payload.remarks)


@router.get("/enrollments", response_model=list[EnrollmentResponse])
def list_enrollments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Enrollment).order_by(Enrollment.enrolled_at.desc())
    if current_user.role == "TRAINEE":
        query = query.where(Enrollment.trainee_id == current_user.id)
    return db.scalars(query).all()


@router.post("/enrollments", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_enrollment(payload: EnrollmentCreate, db: Session = Depends(get_db), _user: User = Depends(PROGRAMME_MANAGERS)):
    get_batch_or_404(db, payload.batch_id)
    existing = db.scalar(select(Enrollment).where(Enrollment.batch_id == payload.batch_id, Enrollment.trainee_id == payload.trainee_id))
    if existing:
        return existing
    enrollment = Enrollment(**payload.model_dump())
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.get("/courses", response_model=list[CourseResponse])
def list_courses(programme_id: int | None = None, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    query = select(TrainingCourse).order_by(TrainingCourse.id.desc())
    if programme_id:
        query = query.where(TrainingCourse.programme_id == programme_id)
    return db.scalars(query).all()

@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(payload: CourseCreate, db: Session = Depends(get_db), _user: User = Depends(PROGRAMME_MANAGERS)):
    get_programme_or_404(db, payload.programme_id)
    existing = db.scalar(select(TrainingCourse).where(TrainingCourse.programme_id == payload.programme_id, TrainingCourse.course_code == payload.course_code.strip()))
    if existing:
        raise HTTPException(status_code=409, detail="Course code already exists for this programme")
    data = payload.model_dump(); data["course_code"] = data["course_code"].strip(); data["title"] = data["title"].strip()
    course = TrainingCourse(**data); db.add(course); db.commit(); db.refresh(course); return course

@router.get("/course-modules", response_model=list[CourseModuleResponse])
def list_course_modules(course_id: int | None = None, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    query = select(CourseModule).order_by(CourseModule.course_id, CourseModule.module_number)
    if course_id: query = query.where(CourseModule.course_id == course_id)
    return db.scalars(query).all()

@router.post("/course-modules", response_model=CourseModuleResponse, status_code=status.HTTP_201_CREATED)
def create_course_module(payload: CourseModuleCreate, db: Session = Depends(get_db), _user: User = Depends(PROGRAMME_MANAGERS)):
    if not db.get(TrainingCourse, payload.course_id): raise HTTPException(status_code=404, detail="Course not found")
    if db.scalar(select(CourseModule).where(CourseModule.course_id == payload.course_id, CourseModule.module_number == payload.module_number)):
        raise HTTPException(status_code=409, detail="Module number already exists for this course")
    module = CourseModule(**payload.model_dump()); db.add(module); db.commit(); db.refresh(module); return module

@router.get("/course-lessons", response_model=list[CourseLessonResponse])
def list_course_lessons(module_id: int | None = None, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    query = select(CourseLesson).order_by(CourseLesson.module_id, CourseLesson.lesson_number)
    if module_id: query = query.where(CourseLesson.module_id == module_id)
    return db.scalars(query).all()

@router.post("/course-lessons", response_model=CourseLessonResponse, status_code=status.HTTP_201_CREATED)
def create_course_lesson(payload: CourseLessonCreate, db: Session = Depends(get_db), _user: User = Depends(PROGRAMME_MANAGERS)):
    if not db.get(CourseModule, payload.module_id): raise HTTPException(status_code=404, detail="Course module not found")
    if db.scalar(select(CourseLesson).where(CourseLesson.module_id == payload.module_id, CourseLesson.lesson_number == payload.lesson_number)):
        raise HTTPException(status_code=409, detail="Lesson number already exists for this module")
    lesson = CourseLesson(**payload.model_dump()); db.add(lesson); db.commit(); db.refresh(lesson); return lesson
