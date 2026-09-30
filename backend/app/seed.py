from datetime import date, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.institutions.models import Institution
from app.training.models import Enrollment, Nomination, TrainingBatch, TrainingProgramme, TrainingCourse, CourseModule, CourseLesson, ParticipantProfile
from app.training.schedule_models import TrainingSchedule
from app.attendance.models import AttendanceSession
from app.lms.models import Assessment, AssessmentQuestion, AssessmentOption
from app.users.models import User
from app.careers.models import JobPosting
from app.careers.profile_models import CareerProfile


def seed():
    db = SessionLocal()
    try:
        institution = db.scalar(select(Institution).where(Institution.name == "VAMNICOM"))
        if not institution:
            institution = Institution(
                name="VAMNICOM",
                institution_type="NCCT Institute",
                state="Maharashtra",
                district="Pune",
            )
            db.add(institution)
            db.flush()

        users = [
            ("NCCT Administrator", "admin@ncct.local", "NCCT_ADMIN", None, "Admin@123"),
            ("Training Coordinator", "trainer@ncct.local", "TRAINER", institution.id, "Trainer@123"),
            ("Demo Trainee", "trainee@ncct.local", "TRAINEE", institution.id, "Trainee@123"),
            ("Demo Employer", "employer@ncct.local", "EMPLOYER", institution.id, "Employer@123"),
        ]
        for full_name, email, role, institution_id, password in users:
            if not db.scalar(select(User).where(User.email == email)):
                db.add(User(
                    full_name=full_name,
                    email=email,
                    password_hash=hash_password(password),
                    role=role,
                    institution_id=institution_id,
                ))
        db.flush()

        trainer = db.scalar(select(User).where(User.email == "trainer@ncct.local"))
        trainee = db.scalar(select(User).where(User.email == "trainee@ncct.local"))

        programme = db.scalar(select(TrainingProgramme).where(TrainingProgramme.code == "NCCT-COOP-DIGI-01"))
        if not programme:
            programme = TrainingProgramme(
                institution_id=institution.id,
                code="NCCT-COOP-DIGI-01",
                title="Digital Cooperative Management",
                description="Practical training on digital tools, cooperative records and rural enterprise workflows.",
                category="Digital Literacy & Cooperative Management",
                mode="HYBRID",
                duration_days=5,
                capacity=30,
                status="PUBLISHED",
            )
            db.add(programme)
            db.flush()

        batch = db.scalar(select(TrainingBatch).where(TrainingBatch.programme_id == programme.id, TrainingBatch.batch_code == "VAMNICOM-SEP-26-A"))
        if not batch:
            start = date.today() + timedelta(days=7)
            batch = TrainingBatch(
                programme_id=programme.id,
                batch_code="VAMNICOM-SEP-26-A",
                start_date=start,
                end_date=start + timedelta(days=4),
                trainer_id=trainer.id if trainer else None,
                venue="VAMNICOM Training Hall 1",
                capacity=30,
                status="OPEN",
            )
            db.add(batch)
            db.flush()

        nomination = db.scalar(select(Nomination).where(Nomination.batch_id == batch.id, Nomination.trainee_id == trainee.id)) if trainee else None
        if not nomination and trainee:
            nomination = Nomination(
                batch_id=batch.id,
                trainee_id=trainee.id,
                nominated_by_id=trainer.id if trainer else trainee.id,
                status="APPROVED",
                remarks="Demo nomination for the end-to-end Training ERP flow.",
            )
            db.add(nomination)
            db.flush()

        if nomination and trainee and not db.scalar(select(Enrollment).where(Enrollment.batch_id == batch.id, Enrollment.trainee_id == trainee.id)):
            db.add(Enrollment(
                batch_id=batch.id,
                trainee_id=trainee.id,
                nomination_id=nomination.id,
                status="ACTIVE",
            ))

        course = db.scalar(select(TrainingCourse).where(TrainingCourse.programme_id == programme.id, TrainingCourse.course_code == "COOP-DIGI-101"))
        if not course:
            course = TrainingCourse(
                programme_id=programme.id,
                course_code="COOP-DIGI-101",
                title="Digital Cooperative Management Fundamentals",
                description="Demo LMS course covering digital cooperative records, member services and safe online workflows.",
                category="DIGITAL_COOPERATIVE",
                delivery_mode="HYBRID",
                duration_hours=4,
                level="FOUNDATION",
                status="PUBLISHED",
            )
            db.add(course)
            db.flush()

        module_specs = [
            (1, "Digital Cooperative Records", "Understand core digital records and why accurate member data matters.", 90),
            (2, "Safe Digital Workflows", "Apply safe, practical digital workflows for cooperative operations.", 90),
        ]
        for module_number, title, objectives, duration in module_specs:
            module = db.scalar(select(CourseModule).where(CourseModule.course_id == course.id, CourseModule.module_number == module_number))
            if not module:
                module = CourseModule(course_id=course.id, module_number=module_number, title=title, learning_objectives=objectives, duration_minutes=duration)
                db.add(module)
                db.flush()

        lesson_specs = [
            (1, 1, "Introduction to Digital Cooperative Records", "TEXT", 20, True),
            (1, 2, "Member Data and Record Quality", "TEXT", 25, True),
            (2, 1, "Secure Login and Password Practices", "TEXT", 20, True),
            (2, 2, "Digital Service Workflow", "TEXT", 25, True),
        ]
        modules_by_number = {m.module_number: m for m in db.scalars(select(CourseModule).where(CourseModule.course_id == course.id)).all()}
        for module_number, lesson_number, title, content_type, duration, mandatory in lesson_specs:
            module = modules_by_number[module_number]
            lesson = db.scalar(select(CourseLesson).where(CourseLesson.module_id == module.id, CourseLesson.lesson_number == lesson_number))
            if not lesson:
                db.add(CourseLesson(
                    module_id=module.id,
                    lesson_number=lesson_number,
                    title=title,
                    content_type=content_type,
                    duration_minutes=duration,
                    is_mandatory=mandatory,
                ))

        # LMS-02 demo assessments. Questions/options are created idempotently.
        assessment_specs = [
            {
                "lesson_title": "Member Data and Record Quality",
                "title": "Digital Cooperative Records Check",
                "instructions": "Answer all questions. Pass mark is 60%.",
                "pass_mark": 60,
                "questions": [
                    (1, "Which practice most improves the quality of cooperative member records?", [(1, "Keeping records accurate and up to date", True), (2, "Sharing passwords with colleagues", False), (3, "Deleting old records without review", False), (4, "Using duplicate member profiles", False)]),
                    (2, "Why should member data be verified before use?", [(1, "To reduce data quality errors", True), (2, "To make forms longer", False), (3, "To avoid backups", False), (4, "To prevent authorized access", False)]),
                    (3, "Which information should be protected from unauthorized disclosure?", [(1, "Member personal information", True), (2, "Public course title", False), (3, "Published training date", False), (4, "Public institution name", False)]),
                    (4, "What should a staff member do when a member record appears duplicated?", [(1, "Report and resolve it using the approved process", True), (2, "Create another duplicate", False), (3, "Ignore it", False), (4, "Share it publicly", False)]),
                    (5, "A good digital record should be...", [(1, "Accurate, consistent and traceable", True), (2, "Unverified and incomplete", False), (3, "Accessible to everyone", False), (4, "Stored without ownership", False)]),
                ],
            },
            {
                "lesson_title": "Digital Service Workflow",
                "title": "Digital Service Workflow Assessment",
                "instructions": "Choose the best answer for each question.",
                "pass_mark": 60,
                "questions": [
                    (1, "What is a safe first step when handling a digital service request?", [(1, "Verify the request and required information", True), (2, "Share credentials", False), (3, "Skip validation", False), (4, "Publish private data", False)]),
                    (2, "Why are standardized workflows useful?", [(1, "They make processes consistent and auditable", True), (2, "They remove accountability", False), (3, "They prevent record keeping", False), (4, "They require password sharing", False)]),
                    (3, "What should be done with a user's password?", [(1, "Keep it confidential", True), (2, "Write it on a public noticeboard", False), (3, "Send it to an unknown person", False), (4, "Reuse it for all users", False)]),
                    (4, "When should an unusual digital incident be reported?", [(1, "As soon as it is identified through the approved process", True), (2, "Only after deleting evidence", False), (3, "Never", False), (4, "After sharing it publicly", False)]),
                    (5, "A completed digital service record should support...", [(1, "Traceability and follow-up", True), (2, "Uncontrolled access", False), (3, "Missing ownership", False), (4, "Duplicate requests", False)]),
                ],
            },
        ]
        lessons_by_title = {lesson.title: lesson for lesson in db.scalars(
            select(CourseLesson).join(CourseModule, CourseModule.id == CourseLesson.module_id).where(CourseModule.course_id == course.id)
        ).all()}
        for spec in assessment_specs:
            lesson = lessons_by_title.get(spec["lesson_title"])
            if not lesson:
                continue
            assessment = db.scalar(select(Assessment).where(Assessment.lesson_id == lesson.id))
            if not assessment:
                assessment = Assessment(
                    lesson_id=lesson.id, title=spec["title"], instructions=spec["instructions"],
                    pass_mark=spec["pass_mark"], max_attempts=0, status="PUBLISHED"
                )
                db.add(assessment)
                db.flush()
            for question_number, question_text, options in spec["questions"]:
                question = db.scalar(select(AssessmentQuestion).where(
                    AssessmentQuestion.assessment_id == assessment.id,
                    AssessmentQuestion.question_number == question_number,
                ))
                if not question:
                    question = AssessmentQuestion(
                        assessment_id=assessment.id, question_number=question_number,
                        question_text=question_text, marks=1
                    )
                    db.add(question)
                    db.flush()
                for option_number, option_text, is_correct in options:
                    option = db.scalar(select(AssessmentOption).where(
                        AssessmentOption.question_id == question.id,
                        AssessmentOption.option_number == option_number,
                    ))
                    if not option:
                        db.add(AssessmentOption(
                            question_id=question.id, option_number=option_number,
                            option_text=option_text, is_correct=is_correct
                        ))

        # Careers-03 demo participant data for recruiter search.
        # Only fill missing education so existing trainee-entered data is not overwritten.
        if trainee:
            participant_profile = db.scalar(select(ParticipantProfile).where(ParticipantProfile.user_id == trainee.id))
            if not participant_profile:
                participant_profile = ParticipantProfile(
                    user_id=trainee.id,
                    participant_code=f"NCCT-{trainee.id}",
                    participant_type="RURAL_YOUTH",
                    education_level="Graduate",
                    state="Maharashtra",
                    district="Pune",
                    digital_literacy_level="INTERMEDIATE",
                    years_experience=0,
                    profile_status="COMPLETE",
                )
                db.add(participant_profile)
                db.flush()
            elif not participant_profile.education_level:
                participant_profile.education_level = "Graduate"
            if not participant_profile.state:
                participant_profile.state = "Maharashtra"
            if not participant_profile.district:
                participant_profile.district = "Pune"

            career_profile = db.scalar(select(CareerProfile).where(CareerProfile.trainee_id == trainee.id))
            if not career_profile:
                db.add(CareerProfile(
                    trainee_id=trainee.id,
                    headline="Cooperative Digital Services Trainee",
                    professional_summary="Entry-level cooperative professional trained in digital records, member services and safe digital workflows.",
                    skills="Digital records, member services, MS Office, cooperative management",
                    preferred_locations="Pune, Maharashtra; Remote",
                    preferred_employment_types="FULL_TIME; INTERNSHIP",
                    resume_text="Demo resume profile for the NCCT employment exchange.",
                    profile_visibility="VISIBLE",
                ))

        # ERP-08 demo timetable entries.
        schedule_specs = [
            (1, "Digital Cooperative Records", "VAMNICOM Training Hall 1", "IN_PERSON"),
            (2, "Safe Digital Workflows", "VAMNICOM Computer Lab", "HYBRID"),
        ]
        if trainer and batch and not db.scalar(select(TrainingSchedule).where(TrainingSchedule.batch_id == batch.id)):
            for offset, topic, venue, mode in schedule_specs:
                session_date = batch.start_date + timedelta(days=offset - 1)
                db.add(TrainingSchedule(
                    batch_id=batch.id, course_id=course.id, trainer_id=trainer.id,
                    session_date=session_date, start_time=__import__("datetime").time(9, 30),
                    end_time=__import__("datetime").time(11, 0), topic=topic, venue=venue, mode=mode,
                    status="SCHEDULED", notes="Demo ERP-08 timetable entry.", created_by_id=trainer.id,
                ))

        employer = db.scalar(select(User).where(User.email == "employer@ncct.local"))
        if employer:
            demo_job = db.scalar(select(JobPosting).where(JobPosting.title == "Cooperative Digital Services Associate", JobPosting.employer_id == employer.id))
            if not demo_job:
                db.add(JobPosting(
                    employer_id=employer.id,
                    title="Cooperative Digital Services Associate",
                    organization_name="Demo Cooperative Employer",
                    description="Support member-facing digital services, cooperative records and basic reporting workflows.",
                    location="Pune, Maharashtra",
                    employment_type="FULL_TIME",
                    skills="Digital records, member services, MS Office",
                    minimum_education="Graduate",
                    minimum_experience_years=0,
                    salary_range="₹18,000–₹25,000 / month",
                    status="PUBLISHED",
                ))

        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
