from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.lms.models import (
    Assessment,
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentOption,
    AssessmentQuestion,
    LessonProgress,
)
from app.lms.schemas import (
    AssessmentAnswerInput,
    AssessmentAttemptResponse,
    AssessmentQuestionResponse,
    AssessmentResponse,
    AssessmentSubmitRequest,
    AssessmentOptionResponse,
    CourseDetailResponse,
    LessonProgressResponse,
    LessonResponse,
    ModuleResponse,
    MyCourseResponse,
)
from app.training.models import CourseLesson, CourseModule, Enrollment, TrainingBatch, TrainingCourse
from app.users.models import User

router = APIRouter(prefix="/lms", tags=["LMS"])
TRAINEES = require_roles("TRAINEE")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _enrolled_course_ids(db: Session, trainee_id: int) -> set[int]:
    rows = db.execute(
        select(TrainingCourse.id)
        .join(TrainingBatch, TrainingBatch.programme_id == TrainingCourse.programme_id)
        .join(Enrollment, Enrollment.batch_id == TrainingBatch.id)
        .where(
            Enrollment.trainee_id == trainee_id,
            Enrollment.status.in_(["ACTIVE", "COMPLETED"]),
            TrainingCourse.status.in_(["PUBLISHED", "ACTIVE"]),
        )
        .distinct()
    ).scalars().all()
    return set(rows)


def _require_course(db: Session, course_id: int, trainee_id: int) -> TrainingCourse:
    course = db.get(TrainingCourse, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course_id not in _enrolled_course_ids(db, trainee_id):
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")
    if course.status not in {"PUBLISHED", "ACTIVE"}:
        raise HTTPException(status_code=409, detail="This course is not currently published")
    return course


def _course_progress(db: Session, course_id: int, trainee_id: int) -> tuple[int, int, int]:
    total = db.scalar(
        select(func.count(CourseLesson.id))
        .join(CourseModule, CourseModule.id == CourseLesson.module_id)
        .where(CourseModule.course_id == course_id)
    ) or 0
    completed = db.scalar(
        select(func.count(CourseLesson.id))
        .join(CourseModule, CourseModule.id == CourseLesson.module_id)
        .join(LessonProgress, LessonProgress.lesson_id == CourseLesson.id)
        .where(
            CourseModule.course_id == course_id,
            LessonProgress.trainee_id == trainee_id,
            LessonProgress.status == "COMPLETED",
        )
    ) or 0
    percent = round((completed / total) * 100) if total else 0
    return total, completed, percent


def _assessment_for_lesson(db: Session, lesson_id: int) -> Assessment | None:
    return db.scalar(select(Assessment).where(Assessment.lesson_id == lesson_id, Assessment.status == "PUBLISHED"))


def _assessment_questions(db: Session, assessment_id: int) -> list[AssessmentQuestion]:
    return db.scalars(
        select(AssessmentQuestion)
        .where(AssessmentQuestion.assessment_id == assessment_id)
        .order_by(AssessmentQuestion.question_number)
    ).all()


def _assessment_response(db: Session, assessment: Assessment) -> AssessmentResponse:
    questions = _assessment_questions(db, assessment.id)
    question_ids = [q.id for q in questions]
    options = db.scalars(
        select(AssessmentOption)
        .where(AssessmentOption.question_id.in_(question_ids))
        .order_by(AssessmentOption.option_number)
    ).all() if question_ids else []
    options_by_question: dict[int, list[AssessmentOption]] = {q.id: [] for q in questions}
    for option in options:
        options_by_question.setdefault(option.question_id, []).append(option)
    return AssessmentResponse(
        id=assessment.id,
        lesson_id=assessment.lesson_id,
        title=assessment.title,
        instructions=assessment.instructions,
        pass_mark=assessment.pass_mark,
        max_attempts=assessment.max_attempts,
        status=assessment.status,
        question_count=len(questions),
        max_score=sum(q.marks for q in questions),
        questions=[
            AssessmentQuestionResponse(
                id=q.id,
                question_number=q.question_number,
                question_text=q.question_text,
                marks=q.marks,
                options=[
                    AssessmentOptionResponse(id=o.id, option_number=o.option_number, option_text=o.option_text)
                    for o in options_by_question.get(q.id, [])
                ],
            )
            for q in questions
        ],
    )


@router.get("/my-courses", response_model=list[MyCourseResponse])
def my_courses(db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    course_ids = _enrolled_course_ids(db, user.id)
    if not course_ids:
        return []
    courses = db.scalars(
        select(TrainingCourse)
        .where(TrainingCourse.id.in_(course_ids))
        .order_by(TrainingCourse.title)
    ).all()
    result = []
    for course in courses:
        total, completed, percent = _course_progress(db, course.id, user.id)
        result.append(MyCourseResponse(
            course_id=course.id,
            course_code=course.course_code,
            title=course.title,
            programme_id=course.programme_id,
            total_lessons=total,
            completed_lessons=completed,
            progress_percent=percent,
        ))
    return result


@router.get("/courses/{course_id}", response_model=CourseDetailResponse)
def course_detail(course_id: int, db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    course = _require_course(db, course_id, user.id)
    modules = db.scalars(
        select(CourseModule).where(CourseModule.course_id == course.id).order_by(CourseModule.module_number)
    ).all()
    lessons = db.scalars(
        select(CourseLesson)
        .join(CourseModule, CourseModule.id == CourseLesson.module_id)
        .where(CourseModule.course_id == course.id)
        .order_by(CourseModule.module_number, CourseLesson.lesson_number)
    ).all()
    lesson_ids = [lesson.id for lesson in lessons]
    progress_rows = db.scalars(
        select(LessonProgress).where(
            LessonProgress.trainee_id == user.id,
            LessonProgress.lesson_id.in_(lesson_ids),
        )
    ).all() if lesson_ids else []
    progress_by_lesson = {row.lesson_id: row.status for row in progress_rows}
    assessments = db.scalars(
        select(Assessment).where(Assessment.lesson_id.in_(lesson_ids), Assessment.status == "PUBLISHED")
    ).all() if lesson_ids else []
    assessments_by_lesson = {a.lesson_id: a for a in assessments}
    question_counts = {}
    if assessments:
        rows = db.execute(
            select(AssessmentQuestion.assessment_id, func.count(AssessmentQuestion.id))
            .where(AssessmentQuestion.assessment_id.in_([a.id for a in assessments]))
            .group_by(AssessmentQuestion.assessment_id)
        ).all()
        question_counts = {assessment_id: count for assessment_id, count in rows}

    lessons_by_module: dict[int, list[LessonResponse]] = {module.id: [] for module in modules}
    for lesson in lessons:
        assessment = assessments_by_lesson.get(lesson.id)
        lessons_by_module.setdefault(lesson.module_id, []).append(
            LessonResponse(
                id=lesson.id,
                module_id=lesson.module_id,
                lesson_number=lesson.lesson_number,
                title=lesson.title,
                content_type=lesson.content_type,
                content_url=lesson.content_url,
                duration_minutes=lesson.duration_minutes,
                is_mandatory=lesson.is_mandatory,
                status=progress_by_lesson.get(lesson.id, "NOT_STARTED"),
                assessment_id=assessment.id if assessment else None,
                assessment_title=assessment.title if assessment else None,
                assessment_question_count=question_counts.get(assessment.id, 0) if assessment else 0,
                assessment_pass_mark=assessment.pass_mark if assessment else None,
            )
        )
    total, completed, percent = _course_progress(db, course.id, user.id)
    return CourseDetailResponse(
        id=course.id,
        programme_id=course.programme_id,
        course_code=course.course_code,
        title=course.title,
        description=course.description,
        category=course.category,
        delivery_mode=course.delivery_mode,
        duration_hours=course.duration_hours,
        level=course.level,
        status=course.status,
        modules=[ModuleResponse(
            id=module.id,
            course_id=module.course_id,
            module_number=module.module_number,
            title=module.title,
            learning_objectives=module.learning_objectives,
            duration_minutes=module.duration_minutes,
            lessons=lessons_by_module.get(module.id, []),
        ) for module in modules],
        total_lessons=total,
        completed_lessons=completed,
        progress_percent=percent,
    )


@router.get("/courses/{course_id}/progress", response_model=list[LessonProgressResponse])
def course_progress(course_id: int, db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    _require_course(db, course_id, user.id)
    return db.scalars(
        select(LessonProgress)
        .join(CourseLesson, CourseLesson.id == LessonProgress.lesson_id)
        .join(CourseModule, CourseModule.id == CourseLesson.module_id)
        .where(LessonProgress.trainee_id == user.id, CourseModule.course_id == course_id)
        .order_by(CourseModule.module_number, CourseLesson.lesson_number)
    ).all()


@router.post("/lessons/{lesson_id}/start", response_model=LessonProgressResponse)
def start_lesson(lesson_id: int, db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    lesson = db.get(CourseLesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    module = db.get(CourseModule, lesson.module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Course module not found")
    _require_course(db, module.course_id, user.id)
    now = _now()
    progress = db.scalar(select(LessonProgress).where(LessonProgress.trainee_id == user.id, LessonProgress.lesson_id == lesson.id))
    if not progress:
        progress = LessonProgress(trainee_id=user.id, lesson_id=lesson.id, status="IN_PROGRESS", started_at=now, last_accessed_at=now)
        db.add(progress)
    elif progress.status != "COMPLETED":
        progress.status = "IN_PROGRESS"
        progress.started_at = progress.started_at or now
        progress.last_accessed_at = now
    else:
        progress.last_accessed_at = now
    db.commit()
    db.refresh(progress)
    return progress


@router.post("/lessons/{lesson_id}/complete", response_model=LessonProgressResponse)
def complete_lesson(lesson_id: int, db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    lesson = db.get(CourseLesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    module = db.get(CourseModule, lesson.module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Course module not found")
    _require_course(db, module.course_id, user.id)
    now = _now()
    progress = db.scalar(select(LessonProgress).where(LessonProgress.trainee_id == user.id, LessonProgress.lesson_id == lesson.id))
    if not progress:
        progress = LessonProgress(trainee_id=user.id, lesson_id=lesson.id, status="COMPLETED", started_at=now, completed_at=now, last_accessed_at=now)
        db.add(progress)
    else:
        progress.status = "COMPLETED"
        progress.started_at = progress.started_at or now
        progress.completed_at = progress.completed_at or now
        progress.last_accessed_at = now
    db.commit()
    db.refresh(progress)
    return progress


@router.get("/lessons/{lesson_id}/assessment", response_model=AssessmentResponse)
def get_lesson_assessment(lesson_id: int, db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    lesson = db.get(CourseLesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    module = db.get(CourseModule, lesson.module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Course module not found")
    _require_course(db, module.course_id, user.id)
    assessment = _assessment_for_lesson(db, lesson_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="No published assessment for this lesson")
    return _assessment_response(db, assessment)


@router.post("/assessments/{assessment_id}/submit", response_model=AssessmentAttemptResponse)
def submit_assessment(
    assessment_id: int,
    payload: AssessmentSubmitRequest,
    db: Session = Depends(get_db),
    user: User = Depends(TRAINEES),
):
    assessment = db.get(Assessment, assessment_id)
    if not assessment or assessment.status != "PUBLISHED":
        raise HTTPException(status_code=404, detail="Assessment not found")
    lesson = db.get(CourseLesson, assessment.lesson_id)
    module = db.get(CourseModule, lesson.module_id) if lesson else None
    if not lesson or not module:
        raise HTTPException(status_code=404, detail="Assessment lesson not found")
    _require_course(db, module.course_id, user.id)

    attempt_count = db.scalar(
        select(func.count(AssessmentAttempt.id)).where(
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.trainee_id == user.id,
        )
    ) or 0
    if assessment.max_attempts > 0 and attempt_count >= assessment.max_attempts:
        raise HTTPException(status_code=409, detail="Maximum assessment attempts reached")

    questions = _assessment_questions(db, assessment.id)
    question_by_id = {q.id: q for q in questions}
    option_ids = {answer.selected_option_id for answer in payload.answers if answer.selected_option_id is not None}
    options = db.scalars(select(AssessmentOption).where(AssessmentOption.id.in_(option_ids))).all() if option_ids else []
    option_by_id = {o.id: o for o in options}

    answer_by_question: dict[int, AssessmentAnswerInput] = {}
    for answer in payload.answers:
        if answer.question_id not in question_by_id:
            raise HTTPException(status_code=400, detail="One or more submitted questions do not belong to this assessment")
        if answer.question_id in answer_by_question:
            raise HTTPException(status_code=400, detail="A question can only be answered once")
        if answer.selected_option_id is not None:
            option = option_by_id.get(answer.selected_option_id)
            if not option or option.question_id != answer.question_id:
                raise HTTPException(status_code=400, detail="One or more selected options are invalid")
        answer_by_question[answer.question_id] = answer

    max_score = sum(q.marks for q in questions)
    score = 0
    for question in questions:
        answer = answer_by_question.get(question.id)
        if answer and answer.selected_option_id is not None:
            option = option_by_id.get(answer.selected_option_id)
            if option and option.is_correct:
                score += question.marks
    percentage = round((score / max_score) * 100) if max_score else 0
    result = "PASS" if percentage >= assessment.pass_mark else "FAIL"

    attempt = AssessmentAttempt(
        assessment_id=assessment.id,
        trainee_id=user.id,
        attempt_number=attempt_count + 1,
        score=score,
        max_score=max_score,
        percentage=percentage,
        result=result,
    )
    db.add(attempt)
    db.flush()

    for question in questions:
        answer = answer_by_question.get(question.id)
        selected = option_by_id.get(answer.selected_option_id) if answer and answer.selected_option_id is not None else None
        is_correct = bool(selected and selected.is_correct)
        db.add(AssessmentAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=selected.id if selected else None,
            is_correct=is_correct,
            awarded_marks=question.marks if is_correct else 0,
        ))

    db.commit()
    db.refresh(attempt)
    return attempt


@router.get("/assessments/{assessment_id}/result", response_model=AssessmentAttemptResponse)
def latest_assessment_result(assessment_id: int, db: Session = Depends(get_db), user: User = Depends(TRAINEES)):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    lesson = db.get(CourseLesson, assessment.lesson_id)
    module = db.get(CourseModule, lesson.module_id) if lesson else None
    if not lesson or not module:
        raise HTTPException(status_code=404, detail="Assessment lesson not found")
    _require_course(db, module.course_id, user.id)
    attempt = db.scalar(
        select(AssessmentAttempt)
        .where(AssessmentAttempt.assessment_id == assessment.id, AssessmentAttempt.trainee_id == user.id)
        .order_by(AssessmentAttempt.attempt_number.desc())
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="No assessment attempt found")
    return attempt
