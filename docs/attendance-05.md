# Attendance-05 — Dashboard Integration

## Scope

Attendance metrics are now surfaced on the central dashboard without creating a new database table or migration.

## Dashboard data

For NCCT administrators, institute administrators, and trainers, the dashboard shows:

- overall attendance rate for the sessions visible to that role
- total sessions
- present count
- late count
- absent count
- number of trainees below the 75% attendance threshold

For trainees, the dashboard shows the trainee's own attendance rate, session count, present/late/absent counts, and whether the trainee is below the 75% threshold.

## Scope rules

- `NCCT_ADMIN`: all attendance sessions
- `INSTITUTE_ADMIN`: sessions belonging to programmes in the user's institution
- `TRAINER`: sessions for batches assigned to the trainer
- `TRAINEE`: only sessions for active enrolments belonging to that trainee
- `EMPLOYER`: attendance is not exposed on the employer dashboard

## Navigation

The dashboard Attendance overview includes a `View attendance` action that opens the existing Attendance module. The detailed Attendance Reports & Analytics screen remains the source for date filters, batch filters, CSV export, and low-attendance details.

## Database

No Alembic migration is required. Attendance-05 reads the existing attendance sessions, attendance records, and active enrolments.

## Verification

Backend Python files should be syntax-compiled before handoff. The frontend must be tested with `npm install` and `npm run build` on the development laptop because `node_modules` is intentionally excluded from the ZIP.
