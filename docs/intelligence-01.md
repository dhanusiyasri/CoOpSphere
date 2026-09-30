# Intelligence-01 — Capacity & Employment Intelligence

## Scope

Provides a descriptive operational dashboard across the existing NCCT Training ERP, LMS, credentials and employment exchange data.

## API

`GET /api/v1/intelligence/overview`

Roles: `NCCT_ADMIN`, `INSTITUTE_ADMIN`, `TRAINER`.

## Indicators

- Trainee count
- Programme and batch counts
- Active enrollments
- Course and lesson counts
- Completed lesson records and lesson activity rate
- Assessment attempts and pass rate
- Credentials issued
- Published jobs and total applications
- Selected applications and application conversion rate
- Application status distribution
- Recent programme register with batch counts

The dashboard reports current database counts. It does not make forecasts or rank institutions, programmes, trainers, employers or trainees.

## Database

No new migration is required. Intelligence reads the existing ERP, LMS, credentials and careers tables.
