import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.credentials.models import Credential
from app.credentials.schemas import (
    CredentialEligibilityResponse,
    CredentialResponse,
    CredentialRegistryResponse,
    CredentialReadinessResponse,
    CredentialRevokeRequest,
    CredentialVerificationResponse,
)
from app.lms.models import Assessment, AssessmentAttempt, LessonProgress
from app.attendance.models import AttendanceRecord, AttendanceSession
from app.training.models import CourseLesson, CourseModule, Enrollment, TrainingBatch, TrainingCourse, TrainingProgramme
from app.users.models import User
from app.core.config import settings

router = APIRouter(prefix="/credentials", tags=["Skills & Credentials"])
TRAINEES = require_roles("TRAINEE")
MANAGERS = require_roles("NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER")


def _enrolled_course(db: Session, course_id: int, trainee_id: int) -> TrainingCourse:
    course = db.get(TrainingCourse, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    enrolled = db.scalar(
        select(Enrollment.id)
        .join(TrainingBatch, TrainingBatch.id == Enrollment.batch_id)
        .where(
            Enrollment.trainee_id == trainee_id,
            Enrollment.status.in_(["ACTIVE", "COMPLETED"]),
            TrainingBatch.programme_id == course.programme_id,
        )
        .limit(1)
    )
    if not enrolled:
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")
    return course


def _eligibility(db: Session, course: TrainingCourse, trainee_id: int) -> tuple[bool, int, int, int, str | None]:
    lessons = db.scalars(
        select(CourseLesson)
        .join(CourseModule, CourseModule.id == CourseLesson.module_id)
        .where(CourseModule.course_id == course.id)
        .order_by(CourseModule.module_number, CourseLesson.lesson_number)
    ).all()
    total_lessons = len(lessons)
    completed_lessons = db.scalar(
        select(func.count(CourseLesson.id))
        .join(CourseModule, CourseModule.id == CourseLesson.module_id)
        .join(LessonProgress, LessonProgress.lesson_id == CourseLesson.id)
        .where(
            CourseModule.course_id == course.id,
            LessonProgress.trainee_id == trainee_id,
            LessonProgress.status == "COMPLETED",
        )
    ) or 0
    if total_lessons == 0 or completed_lessons != total_lessons:
        return False, total_lessons, completed_lessons, 0, "Complete all course lessons first."

    assessments = db.scalars(
        select(Assessment)
        .where(
            Assessment.lesson_id.in_([lesson.id for lesson in lessons]),
            Assessment.status == "PUBLISHED",
        )
    ).all()
    if not assessments:
        return True, total_lessons, completed_lessons, 100, None

    percentages: list[int] = []
    for assessment in assessments:
        latest = db.scalar(
            select(AssessmentAttempt)
            .where(
                AssessmentAttempt.assessment_id == assessment.id,
                AssessmentAttempt.trainee_id == trainee_id,
            )
            .order_by(AssessmentAttempt.attempt_number.desc())
            .limit(1)
        )
        if not latest or latest.result != "PASS":
            return False, total_lessons, completed_lessons, 0, f"Pass the assessment: {assessment.title}."
        percentages.append(latest.percentage)

    score = round(sum(percentages) / len(percentages)) if percentages else 100
    return True, total_lessons, completed_lessons, score, None


def _new_credential_number(db: Session) -> str:
    for _ in range(10):
        value = f"NCCT-{secrets.token_hex(5).upper()}"
        if not db.scalar(select(Credential.id).where(Credential.credential_number == value)):
            return value
    raise HTTPException(status_code=500, detail="Could not generate a unique credential number")


def _credential_verification_url(credential_number: str) -> str:
    return f"{settings.frontend_base_url.rstrip('/')}/verify/{credential_number}"


def _build_certificate_pdf(credential: Credential, trainee_name: str) -> bytes:
    try:
        import io
        import qrcode
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Certificate PDF dependencies are not installed. Run pip install -r requirements.txt.",
        ) from exc

    verification_url = _credential_verification_url(credential.credential_number)
    qr = qrcode.QRCode(version=None, box_size=5, border=2)
    qr.add_data(verification_url)
    qr.make(fit=True)
    qr_buffer = io.BytesIO()
    qr.make_image().save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    output = io.BytesIO()
    width, height = landscape(A4)
    pdf = canvas.Canvas(output, pagesize=(width, height))

    pdf.setTitle(f"NCCT Certificate - {credential.credential_number}")
    pdf.setStrokeColorRGB(0.10, 0.23, 0.43)
    pdf.setLineWidth(2)
    pdf.rect(14 * mm, 14 * mm, width - 28 * mm, height - 28 * mm)
    pdf.setLineWidth(0.5)
    pdf.rect(20 * mm, 20 * mm, width - 40 * mm, height - 40 * mm)

    pdf.setFillColorRGB(0.10, 0.23, 0.43)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(width / 2, height - 42 * mm, "NATIONAL COUNCIL FOR COOPERATIVE TRAINING")

    pdf.setFillColorRGB(0.20, 0.25, 0.33)
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 51 * mm, "Course Completion Certificate")

    pdf.setFillColorRGB(0.08, 0.12, 0.20)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(width / 2, height - 72 * mm, trainee_name)

    pdf.setFillColorRGB(0.35, 0.39, 0.46)
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(width / 2, height - 84 * mm, "has successfully completed the NCCT training course")

    pdf.setFillColorRGB(0.10, 0.23, 0.43)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 98 * mm, credential.course_title)

    pdf.setFillColorRGB(0.20, 0.25, 0.33)
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(70 * mm, 37 * mm, f"Credential: {credential.credential_number}")
    pdf.drawCentredString(width / 2, 37 * mm, f"Score: {credential.score_percentage}%")
    pdf.drawCentredString(width - 70 * mm, 37 * mm, f"Issued: {credential.issued_at.strftime('%d %b %Y')}")

    from reportlab.lib.utils import ImageReader
    pdf.drawImage(ImageReader(qr_buffer), width - 60 * mm, 52 * mm, 32 * mm, 32 * mm, preserveAspectRatio=True, mask='auto')
    pdf.setFont("Helvetica", 7)
    pdf.setFillColorRGB(0.35, 0.39, 0.46)
    pdf.drawString(width - 87 * mm, 49 * mm, "Scan to verify credential")

    pdf.showPage()
    pdf.save()
    return output.getvalue()




def _attendance_percent(db: Session, trainee_id: int, batch_id: int) -> int | None:
    total = db.scalar(
        select(func.count(AttendanceSession.id)).where(AttendanceSession.batch_id == batch_id)
    ) or 0
    if total == 0:
        return None
    attended = db.scalar(
        select(func.count(AttendanceRecord.id))
        .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
        .where(
            AttendanceSession.batch_id == batch_id,
            AttendanceRecord.trainee_id == trainee_id,
            AttendanceRecord.status.in_(["PRESENT", "LATE", "EXCUSED"]),
        )
    ) or 0
    return round((attended / total) * 100)


def _readiness_for(db: Session, trainee: User, course: TrainingCourse, batch: TrainingBatch, attendance_threshold: int) -> CredentialReadinessResponse:
    eligible, total_lessons, completed_lessons, score, reason = _eligibility(db, course, trainee.id)
    lesson_percent = round((completed_lessons / total_lessons) * 100) if total_lessons else 0
    assessments = db.scalars(
        select(Assessment)
        .where(
            Assessment.lesson_id.in_(
                select(CourseLesson.id)
                .join(CourseModule, CourseModule.id == CourseLesson.module_id)
                .where(CourseModule.course_id == course.id)
            ),
            Assessment.status == "PUBLISHED",
        )
    ).all()
    assessment_passed = True
    assessment_scores: list[int] = []
    for assessment in assessments:
        latest = db.scalar(
            select(AssessmentAttempt)
            .where(AssessmentAttempt.assessment_id == assessment.id, AssessmentAttempt.trainee_id == trainee.id)
            .order_by(AssessmentAttempt.attempt_number.desc())
            .limit(1)
        )
        if not latest or latest.result != "PASS":
            assessment_passed = False
        if latest:
            assessment_scores.append(latest.percentage)
    attendance = _attendance_percent(db, trainee.id, batch.id)
    if not reason and attendance is not None and attendance < attendance_threshold:
        reason = f"Attendance is below the {attendance_threshold}% advisory threshold."
    existing = db.scalar(
        select(Credential).where(
            Credential.trainee_id == trainee.id,
            Credential.course_id == course.id,
        )
    )
    readiness_eligible = eligible
    return CredentialReadinessResponse(
        trainee_id=trainee.id, trainee_name=trainee.full_name, trainee_email=trainee.email,
        course_id=course.id, course_code=course.course_code, course_title=course.title,
        batch_id=batch.id, batch_code=batch.batch_code, lesson_completion_percent=lesson_percent,
        completed_lessons=completed_lessons, total_lessons=total_lessons,
        assessment_passed=assessment_passed, assessment_score=(round(sum(assessment_scores)/len(assessment_scores)) if assessment_scores else score),
        attendance_percent=attendance, attendance_threshold=attendance_threshold,
        eligible=readiness_eligible, reason=reason,
        credential_id=existing.id if existing else None,
        credential_number=existing.credential_number if existing else None,
        credential_status=existing.status if existing else None,
    )


@router.get("/readiness", response_model=list[CredentialReadinessResponse])
def credential_readiness(
    attendance_threshold: int = 75,
    course_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(MANAGERS),
):
    if attendance_threshold < 0 or attendance_threshold > 100:
        raise HTTPException(status_code=422, detail="Attendance threshold must be between 0 and 100")
    query = (
        select(Enrollment, User, TrainingBatch, TrainingCourse)
        .join(User, User.id == Enrollment.trainee_id)
        .join(TrainingBatch, TrainingBatch.id == Enrollment.batch_id)
        .join(TrainingCourse, TrainingCourse.programme_id == TrainingBatch.programme_id)
        .where(Enrollment.status.in_(["ACTIVE", "COMPLETED"]))
    )
    if course_id is not None:
        query = query.where(TrainingCourse.id == course_id)
    if user.role == "TRAINER":
        query = query.where(TrainingBatch.trainer_id == user.id)
    elif user.role == "INSTITUTE_ADMIN":
        query = query.join(TrainingProgramme, TrainingProgramme.id == TrainingBatch.programme_id).where(TrainingProgramme.institution_id == user.institution_id)
    rows = db.execute(query).unique().all()
    result = []
    seen: set[tuple[int, int]] = set()
    for enrollment, trainee, batch, course in rows:
        key = (trainee.id, course.id)
        if key in seen:
            continue
        seen.add(key)
        result.append(_readiness_for(db, trainee, course, batch, attendance_threshold))
    result.sort(key=lambda x: (x.eligible, x.attendance_percent if x.attendance_percent is not None else -1, x.trainee_name.lower()))
    return result


@router.get("/courses/{course_id}/eligibility", response_model=CredentialEligibilityResponse)
def credential_eligibility(course_id: int, db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    course = _enrolled_course(db, course_id, user.id)
    eligible, total_lessons, completed_lessons, score, reason = _eligibility(db, course, user.id)
    return CredentialEligibilityResponse(
        course_id=course.id, eligible=eligible, total_lessons=total_lessons,
        completed_lessons=completed_lessons, score_percentage=score, reason=reason
    )


@router.get("/my-credentials", response_model=list[CredentialResponse])
def my_credentials(db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    return db.scalars(
        select(Credential)
        .where(Credential.trainee_id == user.id)
        .order_by(Credential.issued_at.desc())
    ).all()


@router.get("/verify/{credential_number}/qr")
def credential_verification_qr(credential_number: str, db: Session = Depends(get_db)):
    """Return a public QR image that points to the credential verification page."""
    credential = db.scalar(select(Credential).where(Credential.credential_number == credential_number))
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    try:
        import io
        import qrcode
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="QR dependencies are not installed.") from exc
    verification_url = _credential_verification_url(credential.credential_number)
    qr = qrcode.QRCode(version=None, box_size=7, border=3)
    qr.add_data(verification_url)
    qr.make(fit=True)
    buffer = io.BytesIO()
    qr.make_image().save(buffer, format="PNG")
    return Response(content=buffer.getvalue(), media_type="image/png", headers={"Cache-Control": "no-store"})


@router.get("/verify/{credential_number}", response_model=CredentialVerificationResponse, include_in_schema=True)
def verify_credential(credential_number: str, db: Session = Depends(get_db)):
    credential = db.scalar(select(Credential).where(Credential.credential_number == credential_number))
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    trainee = db.get(User, credential.trainee_id)
    if not trainee:
        raise HTTPException(status_code=404, detail="Credential holder not found")

    return CredentialVerificationResponse(
        valid=credential.status == "ISSUED",
        credential_number=credential.credential_number,
        title=credential.title,
        course_title=credential.course_title,
        trainee_name=trainee.full_name,
        score_percentage=credential.score_percentage,
        completed_lessons=credential.completed_lessons,
        total_lessons=credential.total_lessons,
        issued_at=credential.issued_at,
        status=credential.status,
        revoked_at=credential.revoked_at,
        revocation_reason=credential.revocation_reason,
    )



def _manager_credential_scope(query, user: User):
    if user.role == "TRAINER":
        return query.where(TrainingBatch.trainer_id == user.id)
    if user.role == "INSTITUTE_ADMIN":
        return query.where(TrainingProgramme.institution_id == user.institution_id)
    return query


@router.get("/registry", response_model=list[CredentialRegistryResponse])
def credential_registry(db: Session = Depends(get_db), user: User = Depends(MANAGERS)):
    query = (
        select(Credential, User, TrainingCourse, TrainingProgramme, TrainingBatch)
        .join(User, User.id == Credential.trainee_id)
        .join(TrainingCourse, TrainingCourse.id == Credential.course_id)
        .join(TrainingProgramme, TrainingProgramme.id == TrainingCourse.programme_id)
        .join(Enrollment, Enrollment.trainee_id == Credential.trainee_id)
        .join(TrainingBatch, TrainingBatch.id == Enrollment.batch_id)
        .where(TrainingBatch.programme_id == TrainingCourse.programme_id)
        .order_by(Credential.issued_at.desc())
    )
    query = _manager_credential_scope(query, user)
    rows = db.execute(query).unique().all()
    seen: set[int] = set()
    result = []
    for credential, trainee, course, programme, _batch in rows:
        if credential.id in seen:
            continue
        seen.add(credential.id)
        result.append(CredentialRegistryResponse(
            **CredentialResponse.model_validate(credential).model_dump(),
            trainee_name=trainee.full_name,
            trainee_email=trainee.email,
            institution_id=programme.institution_id,
            institution_name=None,
            revoked_at=credential.revoked_at,
            revoked_by_id=credential.revoked_by_id,
            issued_by_id=credential.issued_by_id,
            revocation_reason=credential.revocation_reason,
        ))
    return result


@router.post("/{credential_id}/revoke", response_model=CredentialRegistryResponse)
def revoke_credential(credential_id: int, payload: CredentialRevokeRequest, db: Session = Depends(get_db), user: User = Depends(MANAGERS)):
    reason = payload.reason.strip()
    if len(reason) < 5:
        raise HTTPException(status_code=422, detail="Revocation reason must be at least 5 characters")
    query = (
        select(Credential, User, TrainingCourse, TrainingProgramme, TrainingBatch)
        .join(User, User.id == Credential.trainee_id)
        .join(TrainingCourse, TrainingCourse.id == Credential.course_id)
        .join(TrainingProgramme, TrainingProgramme.id == TrainingCourse.programme_id)
        .join(Enrollment, Enrollment.trainee_id == Credential.trainee_id)
        .join(TrainingBatch, TrainingBatch.id == Enrollment.batch_id)
        .where(Credential.id == credential_id, TrainingBatch.programme_id == TrainingCourse.programme_id)
    )
    query = _manager_credential_scope(query, user)
    row = db.execute(query).unique().first()
    if not row:
        raise HTTPException(status_code=404, detail="Credential not found")
    credential, trainee, course, programme, _batch = row
    if credential.status == "REVOKED":
        raise HTTPException(status_code=409, detail="Credential is already revoked")
    credential.status = "REVOKED"
    credential.revoked_at = datetime.now(timezone.utc)
    credential.revoked_by_id = user.id
    credential.revocation_reason = reason
    db.commit()
    db.refresh(credential)
    return CredentialRegistryResponse(
        **CredentialResponse.model_validate(credential).model_dump(),
        trainee_name=trainee.full_name, trainee_email=trainee.email,
        institution_id=programme.institution_id, institution_name=None,
        revoked_at=credential.revoked_at, revoked_by_id=credential.revoked_by_id,
        issued_by_id=credential.issued_by_id, revocation_reason=credential.revocation_reason,
    )



@router.post("/readiness/{trainee_id}/{course_id}/issue", response_model=CredentialResponse)
def issue_ready_credential(
    trainee_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(MANAGERS),
):
    """Issue a credential for a manager-scoped trainee/course that is academically eligible.

    Attendance remains advisory and is deliberately not used as a hard issuance gate.
    """
    trainee = db.get(User, trainee_id)
    if not trainee or trainee.role != "TRAINEE":
        raise HTTPException(status_code=404, detail="Trainee not found")
    course = db.get(TrainingCourse, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    query = (
        select(Enrollment, TrainingBatch)
        .join(TrainingBatch, TrainingBatch.id == Enrollment.batch_id)
        .where(
            Enrollment.trainee_id == trainee_id,
            Enrollment.status.in_(["ACTIVE", "COMPLETED"]),
            TrainingBatch.programme_id == course.programme_id,
        )
        .order_by(Enrollment.id.desc())
    )
    if user.role == "TRAINER":
        query = query.where(TrainingBatch.trainer_id == user.id)
    elif user.role == "INSTITUTE_ADMIN":
        query = query.join(TrainingProgramme, TrainingProgramme.id == TrainingBatch.programme_id).where(
            TrainingProgramme.institution_id == user.institution_id
        )
    enrollment_batch = db.execute(query).first()
    if not enrollment_batch:
        raise HTTPException(status_code=403, detail="Trainee/course is outside your credential scope")
    _enrollment, batch = enrollment_batch

    existing = db.scalar(
        select(Credential).where(
            Credential.trainee_id == trainee_id,
            Credential.course_id == course_id,
        )
    )
    if existing:
        if existing.status == "REVOKED":
            raise HTTPException(status_code=409, detail="A credential already exists for this trainee and course and is revoked. Review the registry before issuing another credential.")
        raise HTTPException(status_code=409, detail=f"Credential {existing.credential_number} is already issued for this trainee and course.")

    eligible, total_lessons, completed_lessons, score, reason = _eligibility(db, course, trainee_id)
    if not eligible:
        raise HTTPException(status_code=409, detail=reason or "Credential requirements are not yet complete.")

    credential = Credential(
        trainee_id=trainee_id,
        course_id=course.id,
        credential_number=_new_credential_number(db),
        title="NCCT Course Completion Credential",
        course_title=course.title,
        status="ISSUED",
        score_percentage=score,
        completed_lessons=completed_lessons,
        total_lessons=total_lessons,
        issued_by_id=user.id,
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)
    return credential


@router.get("/{credential_id}", response_model=CredentialResponse)
def get_credential(credential_id: int, db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    credential = db.get(Credential, credential_id)
    if not credential or credential.trainee_id != user.id:
        raise HTTPException(status_code=404, detail="Credential not found")
    return credential


@router.get("/{credential_id}/certificate.pdf")
def download_certificate(credential_id: int, db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    credential = db.get(Credential, credential_id)
    if not credential or credential.trainee_id != user.id or credential.status != "ISSUED":
        raise HTTPException(status_code=404, detail="Credential not found or no longer active")

    pdf = _build_certificate_pdf(credential, user.full_name)
    filename = f"{credential.credential_number}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/courses/{course_id}/issue", response_model=CredentialResponse)
def issue_credential(course_id: int, db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    course = _enrolled_course(db, course_id, user.id)
    existing = db.scalar(
        select(Credential).where(
            Credential.trainee_id == user.id,
            Credential.course_id == course_id,
        )
    )
    if existing:
        return existing

    eligible, total_lessons, completed_lessons, score, _reason = _eligibility(db, course, user.id)
    if not eligible:
        raise HTTPException(
            status_code=409,
            detail="Credential is not yet eligible. Complete all course lessons and pass all published assessments.",
        )

    credential = Credential(
        trainee_id=user.id,
        course_id=course.id,
        credential_number=_new_credential_number(db),
        title="NCCT Course Completion Credential",
        course_title=course.title,
        status="ISSUED",
        score_percentage=score,
        completed_lessons=completed_lessons,
        total_lessons=total_lessons,
        issued_by_id=user.id,
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)
    return credential
