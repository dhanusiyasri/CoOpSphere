# CERT-02 — Credential Readiness & Issuance Queue

Adds a manager-facing readiness queue on top of the existing credential eligibility/issuance flow.

## What it shows
- trainee and course/batch
- lesson completion
- published assessment pass status and score
- attendance percentage for the trainee's batch (advisory only)
- readiness state and blocking reason
- configurable attendance threshold for the advisory display

## API
- `GET /api/v1/credentials/readiness`

Query parameters:
- `attendance_threshold` (0-100, default 75)
- `course_id` (optional)

Manager scoping:
- NCCT_ADMIN: all records
- INSTITUTE_ADMIN: their institution
- TRAINER: assigned batches

No database migration is required. Existing credential issuance rules remain unchanged: trainees claim credentials from the LMS after completing all lessons and passing published assessments. Attendance is surfaced as an advisory signal in CERT-02 and is not silently added as a new issuance gate.
