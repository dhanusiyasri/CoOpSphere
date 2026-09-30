# LMS-02 — Assessments & Quizzes

LMS-02 adds a complete trainee assessment slice on top of LMS-01.

## Included

- One published assessment per lesson
- Questions and multiple-choice options
- Configurable pass mark
- Unlimited or bounded attempts (`max_attempts = 0` means unlimited)
- Automatic scoring
- PASS / FAIL result persistence
- Attempt and answer persistence
- Trainee-only assessment APIs
- Assessment metadata shown beside lessons
- Trainee assessment UI and saved result

## API

- `GET /api/v1/lms/lessons/{lesson_id}/assessment`
- `POST /api/v1/lms/assessments/{assessment_id}/submit`
- `GET /api/v1/lms/assessments/{assessment_id}/result`

## Database

Migration: `0005_lms_assessments`

Tables:

- `lms_assessments`
- `lms_assessment_questions`
- `lms_assessment_options`
- `lms_assessment_attempts`
- `lms_assessment_answers`

The migration is deliberately hand-written so Alembic does not remove unrelated existing ERP constraints.

## Demo content

The seed script adds two assessments to the demo course:

- Digital Cooperative Records Check
- Digital Service Workflow Assessment

Each has five multiple-choice questions and a 60% pass mark.
