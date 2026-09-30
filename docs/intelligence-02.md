# Intelligence-02 — Institution, Trainer & Programme Drill-down

Adds operational drill-downs to the Intelligence dashboard without introducing a new database migration.

## API
- `GET /api/v1/intelligence/overview`
- `GET /api/v1/intelligence/institutions`
- `GET /api/v1/intelligence/trainers`
- `GET /api/v1/intelligence/programmes/{programme_id}`

All analytics endpoints use the existing analyst roles: `NCCT_ADMIN`, `INSTITUTE_ADMIN`, `TRAINER`.

## UI
- Overview tab with existing capacity, learning, assessment and employment indicators.
- Institutions tab with programme, batch, trainee and active-enrollment counts.
- Trainers tab with assigned batches, active batches and distinct trainees.
- Programme register rows open a programme drill-down showing institution, courses, trainees, enrollments, completed lesson records, credentials and batch occupancy.

No new Alembic migration is required.
