# Dashboard-01 — Central NCCT Workspace

This slice replaces the generic Dashboard placeholder with a role-aware operational dashboard.

## Endpoint

`GET /api/v1/dashboard/summary`

The endpoint uses the authenticated user's role.

- `TRAINEE`: active enrolments, completed lessons, credentials, applications, and recent personal credential/application activity.
- `EMPLOYER`: employer-owned jobs, published opportunities, applications, selected applications, and job-level application counts.
- Other authenticated roles: NCCT operational counts spanning trainees, programmes, batches, active enrolments, courses, credentials, published jobs and lesson completion.

No database migration is required.

Dashboard figures are descriptive operational counts from the current database. They are not forecasts or performance rankings.
