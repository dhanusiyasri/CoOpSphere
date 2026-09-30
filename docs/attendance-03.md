# Attendance-03 — Reports & Analytics

## Purpose
Adds reporting on top of the existing attendance session and record tables. No new database tables or migration are required.

## Manager report
Manager roles (`NCCT_ADMIN`, `INSTITUTE_ADMIN`, `TRAINER`) can open **Attendance → Reports & analytics**.

Filters:
- From date
- To date
- Batch ID (manager view)

Outputs:
- Overall attendance rate
- Session count
- Present / Late / Absent / Exceptions
- Batch performance
- Trainee attendance percentages
- Session-level attendance
- QR check-in and manual-mark counts in the API summary

Trainer reports are scoped to batches assigned to that trainer. Institute-admin reports are scoped to programmes belonging to the admin's institution.

## Trainee report
A trainee can open the same tab to see only their own attendance history, summary and batch breakdown.

## CSV export
The browser can export:
- session report CSV
- trainee report CSV

Exports are generated locally from the report response; no extra server-side file storage is needed.

## API
- `GET /api/v1/attendance/reports`
- `GET /api/v1/attendance/reports/my`

Optional query parameters:
- `from_date=YYYY-MM-DD`
- `to_date=YYYY-MM-DD`
- `batch_id=<id>` on the manager report

## Migration
No migration is needed. Attendance-03 derives analytics from the existing attendance sessions, attendance records and training enrollments.

## Validation
- Backend attendance router/schema files pass Python syntax compilation in the build environment.
- Full frontend build cannot be claimed here because this artifact does not include `node_modules`; run `npm install` and `npm run build` on the target laptop.
