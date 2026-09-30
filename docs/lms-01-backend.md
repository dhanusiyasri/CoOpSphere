# LMS-01 Backend Foundation

This build extends the Training ERP v5 / ERP-07 course-curriculum baseline with the LMS-01 backend foundation.

## Included

- `backend/app/lms/models.py` — trainee lesson progress persistence.
- `backend/app/lms/schemas.py` — LMS API response models.
- `backend/app/lms/router.py` — trainee LMS endpoints.
- `backend/app/main.py` — LMS router registration.
- `backend/alembic/env.py` — LMS model registration for future Alembic autogeneration.
- `backend/alembic/versions/d47869571d78_lms_01_lesson_progress.py` — LMS-01 migration.

## LMS endpoints

- `GET /api/v1/lms/my-courses`
- `GET /api/v1/lms/courses/{course_id}`
- `GET /api/v1/lms/courses/{course_id}/progress`
- `POST /api/v1/lms/lessons/{lesson_id}/start`
- `POST /api/v1/lms/lessons/{lesson_id}/complete`

Learning endpoints are restricted to users with the `TRAINEE` role and require an active/completed enrollment in a batch belonging to the course's programme.

## Migration state

The LMS-01 migration revision is `d47869571d78` and follows `0004_training_courses`.

If the database has already been upgraded to `d47869571d78`, do not run the migration again. On another developer database, run:

```powershell
cd backend
alembic upgrade head
```

## Scope note

This package adds the LMS backend foundation only. The main frontend LMS navigation remains the existing placeholder until the LMS UI slice is implemented.
