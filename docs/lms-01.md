# LMS-01 — Trainee Learning Flow

## Scope

LMS-01 is the first working LMS slice. It deliberately reuses the Training ERP course curriculum and enrollment records rather than creating a second course model.

### Flow

`Trainee → My Courses → Course → Module → Lesson → Start → Complete → Progress %`

### Backend

- `GET /api/v1/lms/my-courses`
- `GET /api/v1/lms/courses/{course_id}`
- `GET /api/v1/lms/courses/{course_id}/progress`
- `POST /api/v1/lms/lessons/{lesson_id}/start`
- `POST /api/v1/lms/lessons/{lesson_id}/complete`

Learning endpoints require the `TRAINEE` role. A course is available when the trainee has an active or completed enrollment in a batch belonging to the course's programme and the course is published/active.

### Persistence

Migration `d47869571d78_lms_01_lesson_progress` creates `training_lesson_progress` with a unique `(trainee_id, lesson_id)` pair. Lesson states are `NOT_STARTED`, `IN_PROGRESS`, and `COMPLETED`.

### Frontend

The LMS navigation item opens the trainee workspace with:

- My Courses list and progress bars
- Course/module/lesson hierarchy
- Lesson state indicators
- Start and Complete actions
- Saved course progress percentage

Video hosting, SCORM, quizzes, certificates, offline synchronization, AI tutoring and analytics are intentionally outside LMS-01 and can be implemented as later slices.
